from ..schemas.tasks import TaskCreate, TaskOut
from datetime import datetime
from typing import List
from fastapi.encoders import jsonable_encoder


class TasksDB:
    """Database Manager for Tasks

    Takes a connection (only tested with Postgres) and exposes common CRUD functions.
    """

    def __init__(self, connection, table_name):
        self.connection = connection
        self.table_name = table_name

    def create(self, task: TaskCreate) -> TaskOut:
        sql = f'''
        INSERT INTO {self.table_name} ({', '.join(list(task.__fields__))})
        VALUES {tuple(getattr(task, field) for field in list(task.__fields__))}
        RETURNING *;
        '''
        with self.connection.connect() as conn:
            return conn.execute(sql).fetchone()

    def read_all(self) -> List[TaskOut]:
        sql = f'''
        SELECT {", ".join(list(TaskOut.__fields__))} FROM {self.table_name}
        WHERE complete_date IS NULL
        ORDER BY priority, add_date;
        '''
        with self.connection.connect() as c:
            return c.execute(sql).fetchall()

    def read_one(self, task_id: int) -> TaskOut:
        sql = f'''
        SELECT {", ".join(list(TaskOut.__fields__))} FROM {self.table_name}
        WHERE id = {task_id};
        '''
        with self.connection.connect() as c:
            return c.execute(sql).fetchone()

    def update(self, task: TaskOut) -> TaskOut:
        def stringify(x):
            return f"'{x}'" if isinstance(x, (str, datetime)) else x

        sql = f'''
        UPDATE {self.table_name}
        SET {", ".join([f'{k} = {stringify(v)}' for k, v in task.dict().items()])}
        WHERE {task.id} = id
        RETURNING *
        '''
        sql.replace('None', 'NULL')
        with self.connection.connect() as c:
            return c.execute(sql).fetchone()

    def delete(self, task_id):
        sql = f'''
        DELETE FROM {self.table_name}
        WHERE id = {task_id};
        '''
        with self.connection.connect() as c:
            c.execute(sql)
