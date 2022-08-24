import time

import docker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import CreateSchema

from euphoria.backend.common.db.sqlalchemy.base_class import Base
from euphoria.backend.common.models.tasks import Task

client = docker.DockerClient()

testdb = client.containers.run(
    'postgres:14',
    detach=True,
    environment={
        'ENVIRONMENT': 'development',
        'POSTGRES_USER': 'postgres',
        'POSTGRES_PASSWORD': 'postgres',
    },
    name='testdb',
    ports={5432: 5434},
    mem_limit='2g',
    auto_remove=True,
)
time.sleep(1)
engine = create_engine("postgresql://postgres:postgres@localhost:5434", echo=False, future=True)
SessionTesting = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

schemas = ['apartments', 'habits', 'moving', 'portfolio', 'priorities', 'tasks', 'tracks']
with SessionTesting() as session:
    # session.execute(text("CREATE DATABASE euphoria"))
    for schema_name in schemas:
        session.execute(CreateSchema(schema_name))
    session.commit()

Base.metadata.create_all(engine)


def create_tasks_test_database(num: int = 10):
    return [
        {"name": f"task-{num}", "category": f"category-{num}", "priority": num}
        for num in range(num)
    ]


TASKS_TO_CREATE = create_tasks_test_database()

with SessionTesting() as session:
    for task in TASKS_TO_CREATE:
        session.add(Task(**task))
    session.commit()

with SessionTesting() as session:
    print(session.query(Task).all())

testdb.stop()
