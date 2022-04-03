class PrioritiesDBManager:
    def __init__(self, conn):
        self.conn = conn

    def _execute(self, sql, values=None):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(sql, values or [])
        return cursor

    def df(self, sql):
        cursor = self._execute(sql)
        columns = [col.name for col in cursor.description]
        records = cursor.fetchall()
        return pd.DataFrame(data=records, columns=columns).set_index('id')

    def add_task(self, task):
        sql = '''
        insert into tasks 
            (name, category, subcategory1, subcategory2, priority, add_date, complete_date)
        values (%s, %s, %s, %s, %s, %s, %s)
        '''
        values = (
            task.name,
            task.category,
            task.subcategory1,
            task.subcategory2,
            task.priority,
            task.add_date,
            task.complete_date,
        )
        self._execute(sql, values)

    def complete_task(self, task_id):
        print(self._execute(f'select * from tasks where id = {task_id}').fetchone())
        sql = f'''
        update tasks
        set complete_date = CURRENT_TIMESTAMP
        where id = {task_id}
        '''
        self._execute(sql)
        print(self._execute(f'select * from tasks where id = {task_id}').fetchone())

    def get_top_5_tasks(self):
        c = self._execute(
            '''
            select *
            from tasks
            where complete_date is null
            order by priority, add_date
            limit 5;
            '''
        )
        return c.fetchall()

    def completed_tasks(self):
        return self.df(
            '''
            select * from tasks
            where complete_date is not null
            order by complete_date
            '''
        )