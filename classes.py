import random
from dataclasses import dataclass, field
from typing import List

from student import Student


@dataclass
class Class(object):
    class_id: int
    grade: int
    cohort: str
    period: int
    students: List[Student] = field(default_factory=list)

    @property
    def class_size(self):
        return len(self.students)

    def assign_student(self, student: Student):
        student.clazz.append(self.class_id)
        self.students.append(student)


class ClassFactory(object):

    class SingletonClassFactory(object):
        GRADES = [9, 10, 11, 12]

        def __init__(self):
            self._class_count = 0

        def class_dict(self, cohort, period, grade):
            if not grade:
                grade = random.choice(self.GRADES)

            next_class = self._class_count
            self._class_count += 1
            return {
                'class_id': next_class,
                'grade': grade,
                'cohort': cohort,
                'period': period
            }

    factory = SingletonClassFactory()

    @staticmethod
    def reset():
        ClassFactory.factory = ClassFactory.SingletonClassFactory()

    @staticmethod
    def build(cohort, period, grade=None) -> Class:
        return Class(**ClassFactory.factory.class_dict(cohort, period, grade))
