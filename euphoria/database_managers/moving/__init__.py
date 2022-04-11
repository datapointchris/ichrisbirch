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

    # Box.query()
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

    # Box.query(box.id = id)
    def get_box(self, id):
        box = self._execute(f'select * from boxes where id = {id}').fetchone()
        return dict(box)

    # db.session.add(Box)
    # db.session.commit()
    def add_box(self, box):
        self._execute(
            '''
            insert into boxes (name, size, liquid, warm, essential)
            values
            (:name, :size, :liquid, :warm, :essential);''',
            params=box,
        )

    # db.session.add(Item)
    # db.session.commit()
    def add_box_item(self, item):
        self._execute(
            '''
            insert into items(box_id, name, essential, warm, liquid)
            values
            (:box_id, :name, :essential, :warm, :liquid);''',
            params=item,
        )

    # Item.query()
    def get_all_items(self):
        rows = self._execute('select * from items').fetchall()
        items = [dict(row) for row in rows]
        return items

    # Item.query(item.box_id = id)
    def get_box_items(self, box_id):
        rows = self._execute(f'select * from items where box_id = {box_id}').fetchall()
        items = [dict(row) for row in rows]
        return items

    # db.session.delete(Item)
    def delete_item(self, box_id, item_id):
        item = self._execute(
            f'''select * from items where box_id = {box_id} and id = {item_id}'''
        ).fetchone()
        if item:
            self._execute(f'delete from items where box_id = {box_id} and id = {item_id}')
            return f'Deleted item: {dict(item)}'
        else:
            return f'No item with box_id: {box_id} and id: {item_id}'

    # db.session.detete(Box)
    def delete_box(self, id):
        box = self._execute(f'select * from boxes where id = {id}').fetchone()
        if box:
            self._execute(f'delete from boxes where id = {id}')
            return f'Deleted box: {dict(box)}'
        else:
            return f'No box with id: {id}'

    def text_search(self, query_text):
        query = f"select * from search_items where name MATCH '{query_text}'"
        rows = self._execute(query).fetchall()
        items = [dict(row) for row in rows]
        return items

    # Unnecessary, probably can do a join or reference
    def get_box_id_mappings(self):
        rows = self._execute('select id, name from boxes').fetchall()
        results = [dict(row) for row in rows]
        mapping = {}
        for result in results:
            id = result.get('id')
            name = result.get('name')
            mapping[id] = name
        return mapping
