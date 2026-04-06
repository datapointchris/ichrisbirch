from ichrisbirch.models import Project

BASE_DATA: list[Project] = [
    Project(name='Alpha Project with description', description='Alpha project description text', position=0),
    Project(name='Beta Project without description', description=None, position=1),
    Project(name='Gamma Project with description', description='Gamma project description text', position=2),
]
