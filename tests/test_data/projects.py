from ichrisbirch.models import Project

BASE_DATA: list[Project] = [
    Project(name='Alpha Project with description', description='Alpha project description text', kind='build', position=0),
    Project(name='Beta Project without description', description=None, kind='chore', position=1),
    Project(name='Gamma Project with description', description='Gamma project description text', kind='life', position=2),
]
