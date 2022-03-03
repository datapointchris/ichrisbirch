import datetime


class Task:
    def __init__(
        self,
        title,
        description,
        priority,
        category,
        sub_category=None,
        insert_time=datetime.datetime.now(),
    ):
        self.new_priority = None


class Category:
    def __init__(self, tasks):
        self.tasks = tasks

    def __iter__(self):
        """This is so it can be iterated for thing in category"""
        return iter(self.tasks)

    def __str__(self):
        pass

    def __repr__(self):
        pass


class ToDoList:
    def __init__(self):
        pass

    def get_categories(self):
        pass


TASKS = [
    'task1',
    'task2',
    'task3',
    'task4',
    'task5',
]


cat = Category(TASKS)

for task in cat:
    print(task)