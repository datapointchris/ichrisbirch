import sqlite3
from euphoria.database_managers.base import SQLiteManager


class BoxDBManager(SQLiteManager):
    """SQLite DB Manager for Moving App"""

    def __init__(self):
        self.app = None
        self.connection = None

    def init_app(self, app):
        self.app = app
        db_file = app.config.get('SQLITE_DATABASE_URI')
        self.connection = sqlite3.connect(db_file, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

    def create_all(self):
        with self.app.open_resource('database_managers/moving/schema.sql') as f:
            sql = f.read().decode('utf-8')
            self.connection.executescript(sql)

    def _execute(self, sql, params=None):
        with self.connection as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor

    def get_all_boxes(self, sort_1=None, sort_2=None):
        query = 'select * from boxes'
        if sort_1:
            query += f' order by {sort_1}'
            if sort_1 != 'id':
                query += ' desc'
            if sort_2:
                query += f', {sort_2} desc'
        rows = self._execute(query).fetchall()
        boxes = [dict(row) for row in rows]
        return boxes

    def get_box(self, id):
        box = self._execute(f'select * from boxes where id = {id}').fetchone()
        return dict(box)

    def add_box(self, box):
        self._execute(
            '''
            insert into boxes (name, size, liquid, warm, essential)
            values
            (:name, :size, :liquid, :warm, :essential);''',
            params=box,
        )

    def add_box_item(self, item):
        self._execute(
            '''
            insert into items(box_id, name, essential, warm, liquid)
            values
            (:box_id, :name, :essential, :warm, :liquid);''',
            params=item,
        )

    def get_all_items(self):
        rows = self._execute('select * from items').fetchall()
        items = [dict(row) for row in rows]
        return items

    def get_box_items(self, box_id):
        rows = self._execute(f'select * from items where box_id = {box_id}').fetchall()
        items = [dict(row) for row in rows]
        return items

    def delete_item(self, box_id, item_id):
        item = self._execute(
            f'''select * from items where box_id = {box_id} and id = {item_id}'''
        ).fetchone()
        if item:
            self._execute(f'delete from items where box_id = {box_id} and id = {item_id}')
            return f'Deleted item: {dict(item)}'
        else:
            return f'No item with box_id: {box_id} and id: {item_id}'

    def delete_box(self, id):
        box = self._execute(f'select * from boxes where id = {id}').fetchone()
        if box:
            self._execute(f'delete from boxes where id = {id}')
            return f'Deleted box: {dict(box)}'
        else:
            return f'No box with id: {id}'

    def print_box(self, id):
        box = self.get_box(id)
        items = [
            f'Item: {item["name"]}, Warm: {item["warm"]}'
            for item in self.get_box_items(id)
        ]
        if not items:
            return f'===== {box["name"]} ====='
        lengths = [len(item) for item in items]
        max_length = max(lengths)
        box_title = f'{box["name"]}'
        left_border_len = max(2, (max_length - len(box_title) // 2) // 2)
        right_border_len = max(2, max_length + 8 - left_border_len - len(box_title))
        title = f'{"="*left_border_len} {box_title} {"="*right_border_len}'
        print(title)
        print(f'|{" "*(len(title) - 2)}|')
        for item, length in zip(items, lengths):
            offset = max_length - length
            print(f'|    {item}{" "*(4+offset)}|')
        print(f'|{" "*(len(title) - 2)}|')
        print('-' * len(title))
        print()

    def text_search(self, query_text):
        query = f"select * from search_items where name MATCH '{query_text}'"
        rows = self._execute(query).fetchall()
        items = [dict(row) for row in rows]
        return items

    def get_box_id_mappings(self):
        rows = self._execute('select id, name from boxes').fetchall()
        results = [dict(row) for row in rows]
        mapping = {}
        for result in results:
            id = result.get('id')
            name = result.get('name')
            mapping[id] = name
        return mapping
