import copy
import csv
import math
import os
import queue
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import List, Dict, DefaultDict, Deque

from beautifultable import BeautifulTable

from classes import ClassFactory, Class
from student import StudentFactory, Student


@dataclass
class SimulationParams(object):
    total_students: int
    students_per_class: int
    cohort_switches: int
    class_size_fudge: float
    class_assignment_retry: int
    outside_grade_probability: Dict[int, float]
    iterations: int
    max_degree: int
    schedule: List[str]
    percentage_in_class: float
    number_of_cohorts: int = 2

    def __post_init__(self):
        self.classes = math.ceil(self.total_students / self.students_per_class * self.class_size_fudge)
        self.students = math.ceil(self.total_students * self.percentage_in_class)

    def printable_metadata(self) -> List[List[str]]:

        output = []

        for annotation in self.__annotations__.keys():
            value = self.__getattribute__(annotation)

            output.append([annotation, str(value)])

        return output


class Simulation(object):

    def _build_classes(self, cohort, period):
        classes = []

        for i in range(9, 13):
            classes.append(ClassFactory.build(cohort, period, grade=i))

        for _ in range(math.ceil(self.config.classes/self.config.number_of_cohorts) - 4):
            classes.append(ClassFactory.build(cohort, period))

        return classes

    def _build_students(self):
        students = []

        for _ in range(self.config.students):
            students.append(StudentFactory.build())

        return students

    @staticmethod
    def _build_grade_dict(class_list):

        grade_dict = defaultdict(list)

        for clazz in class_list:
            grade_dict[clazz.grade].append(clazz)

        return grade_dict

    def _build_switch_queue(self):
        switch_queue = deque()

        for switch in self.switches[:self.config.cohort_switches]:
            switch_queue.append(self.cohort_dict[switch])

        return switch_queue

    def _setup_simulation(self):
        StudentFactory.reset()
        ClassFactory.reset()

        self.students = self._build_students()

        self.cohort_1a = self._build_classes('A', 1)
        self.cohort_1b = self._build_classes('B', 1)
        self.cohort_2a = self._build_classes('A', 2)
        self.cohort_2b = self._build_classes('B', 2)

        self.grade_dict_1a = self._build_grade_dict(self.cohort_1a)
        self.grade_dict_1b = self._build_grade_dict(self.cohort_1b)
        self.grade_dict_2a = self._build_grade_dict(self.cohort_2a)
        self.grade_dict_2b = self._build_grade_dict(self.cohort_2b)

        self.cohort_period_1 = [self.grade_dict_1a, self.grade_dict_1b]
        self.cohort_period_2 = [self.grade_dict_2a, self.grade_dict_2b]

        for student in self.students:
            self.assign_student_to_class(student, self.cohort_period_1)

        for student in self.students:
            self.assign_student_to_class(student, self.cohort_period_2)

        self.cohort_dict = {
            '1A': self.cohort_1a,
            '1B': self.cohort_1b,
            '2A': self.cohort_2a,
            '2B': self.cohort_2b,
        }

        self.switch_queue = self._build_switch_queue()

        print('Simulation Setup Done')

    def __init__(self, config: SimulationParams):
        self.config = config

        self.students = []

        self.cohort_1a = []
        self.cohort_1b = []
        self.cohort_2a = []
        self.cohort_2b = []

        self.grade_dict_1a = defaultdict(list)
        self.grade_dict_1b = defaultdict(list)
        self.grade_dict_2a = defaultdict(list)
        self.grade_dict_2b = defaultdict(list)

        self.switches = self.config.schedule * (math.ceil(self.config.cohort_switches/20))

        self.switch_queue: Deque

        self.cohort_dict: Dict

        self.iteration_dict: Dict[int, List[List[Student]]] = {}

        self._setup_simulation()

    def assign_student_to_class(self, student: Student, cohort_list: List[DefaultDict[int, List[Class]]]):
        grade = student.grade

        if random.random() < 0.5:
            class_dict = cohort_list[0]
        else:
            class_dict = cohort_list[1]

        if random.random() < self.config.outside_grade_probability[grade]:
            if grade == 9:
                grade += 1
            elif grade == 12:
                grade -= 1
            else:
                grade_random = random.random()
                if grade_random <= 0.5:
                    grade -= 1
                else:
                    grade += 1

        # try to assign to proper grade and cohort
        for _ in range(self.config.class_assignment_retry):
            clazz = random.choice(class_dict[grade])

            if clazz.class_size < self.config.students_per_class:
                clazz.assign_student(student)
                return

        # give up and assign to an open class
        assigned_grade_list = cohort_list[0][grade] + cohort_list[1][grade]

        # let's try their grade first
        for clazz in assigned_grade_list:
            if clazz.class_size < self.config.students_per_class:
                clazz.assign_student(student)
                return

        # otherwise we try another grade
        for cohort in cohort_list:
            for class_list in cohort.values():
                for clazz in class_list:
                    if clazz.class_size < self.config.students_per_class:
                        clazz.assign_student(student)
                        return

        # last resort, we just assign to a random class in their correct grade - hopefully this doesn't happen too much
        print('A class will be over capacity')
        clazz = random.choice(class_dict[grade])
        clazz.assign_student(student)

    @staticmethod
    def calculate_average_contacts(students: List[Student]) -> float:

        if len(students) == 0:
            return 0.0

        contact_sum = 0

        for student in students:
            contact_sum += student.contact_number

        return contact_sum / len(students)

    def switch(self):
        print('Switching Cohorts')

        current_cohort = self.switch_queue.popleft()

        for clazz in current_cohort:
            for student in clazz.students:
                class_list_copy = clazz.students.copy()
                class_list_copy.remove(student)

                student.add_contacts(class_list_copy)

        print('Cohort Switching Finished')

    def iterate(self) -> List[List[Student]]:
        student_snapshots = []

        while len(self.switch_queue) != 0:
            self.switch()
            student_snapshots.append(copy.deepcopy(self.students))

        return student_snapshots

    def _get_average_contacts_per_iterations(self) -> List[List[str]]:
        output = [['Trial'] + [f'Day: {i+ 1}' for i in range(self.config.cohort_switches)]]

        for i in range(self.config.iterations):
            average_contacts = []
            for student_snapshots in self.iteration_dict[i]:
                average_contacts.append(self.calculate_average_contacts(student_snapshots))

            output.append([str(i + 1)] + ['{:.2f}'.format(contact) for contact in average_contacts])

        return output

    def _get_degree_by_student_iteration_average(self) -> List[List[str]]:
        output = [['Student'] + [f'Degree: {i + 1}' for i in range(self.config.max_degree)]]

        student_dict: Dict[int, Dict[int, int]] = {}

        for iteration in range(self.config.iterations):

            for student in self.iteration_dict[iteration][-1]:
                degree_dict: Dict[int, int] = student.get_contact_sum_by_degree()

                if student.student_id not in student_dict:
                    student_dict[student.student_id] = degree_dict
                else:
                    for degree, count in degree_dict.items():
                        student_count = student_dict[student.student_id]
                        student_count[degree] = student_count.get(degree, 0) + count

        for student, contacts in student_dict.items():
            contact_list = []
            for i in range(self.config.max_degree):
                contact_list.append('{:.2f}'.format(contacts.get(i + 1, 0) / self.config.iterations))
            output.append([str(student)] + contact_list)

        return output

    def _write_table(self, title: str, output_list: List[List[str]]):
        metadata_table = BeautifulTable()
        table = BeautifulTable()

        metadata = self.config.printable_metadata()

        metadata_table.rows.append(['Metadata:', ''])

        for row in metadata:
            metadata_table.rows.append(row)

        for row in output_list:
            table.rows.append(row)

        print(title)
        print(metadata_table)
        print(table)

    def _write_csv(self, file_name: str, output_list: List[List[str]]):

        with open(file_name, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            metadata = self.config.printable_metadata()

            writer.writerow(['Metadata:'])

            for row in metadata:
                writer.writerow(row)

            writer.writerow([''])

            for row in output_list:
                writer.writerow(row)

    def output_results(self):

        average_contacts = self._get_average_contacts_per_iterations()
        self._write_table('Average Contacts per Iteration:', average_contacts)
        self._write_csv('average_contacts.csv', average_contacts)

        degree_per_student = self._get_degree_by_student_iteration_average()
        self._write_table('Average Degree per Student:', degree_per_student)
        self._write_csv('average_degree_per_student.csv', degree_per_student)

    def simulate(self):

        for i in range(self.config.iterations):
            self.iteration_dict[i] = self.iterate()
            print(f'Finished iteration {i}')
            self._setup_simulation()
