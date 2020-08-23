import random
from sys import maxsize
from dataclasses import dataclass, field
from typing import List, Dict

from faker import Faker


@dataclass
class Student(object):
    student_id: int
    name: str
    grade: int
    clazz: List[int] = field(default_factory=list)
    contacts: Dict[int, int] = field(default_factory=dict)

    @property
    def contact_number(self):
        return len(self.contacts)

    def add_contacts(self, contact_list: List['Student']):
        for student in contact_list:
            self.contacts[student.student_id] = 1

            for student_id, degree in student.contacts.items():
                if student_id not in self.contacts:
                    self.contacts[student_id] = degree + 1
                else:
                    self.contacts[student_id] = min(degree + 1, self.contacts.get(student_id, maxsize))

    def get_contact_sum_by_degree(self) -> Dict[int, int]:
        degree_dict = {}

        for degree in self.contacts.values():
            degree_dict[degree] = degree_dict.get(degree, 0) + 1

        return degree_dict


class StudentFactory(object):
    class SingletonStudentFactory(object):

        GRADES = [9, 10, 11, 12]

        def __init__(self):
            self._student_count = 0
            self._faker = Faker()

        def student_dict(self):
            next_student = self._student_count
            self._student_count += 1
            return {
                'student_id': next_student,
                'name': self._faker.name(),
                'grade': random.choice(self.GRADES)
            }

    factory = SingletonStudentFactory()

    @staticmethod
    def reset():
        StudentFactory.factory = StudentFactory.SingletonStudentFactory()

    @staticmethod
    def build() -> Student:
        return Student(**StudentFactory.factory.student_dict())


