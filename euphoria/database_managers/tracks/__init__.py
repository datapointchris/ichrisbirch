import datetime
import re
import os
from euphoria.tracks.static.base_habits import DEFAULT_HABITS
import pymongo

CLIENT = pymongo.MongoClient(os.environ.get('MONGODB_DATABASE_URI'))


class HabitsDBManager:
    def __init__(self):
        self.coll = None

    def init_app(self, app, db, collection):
        host = app.config.get('MONGODB_DATABASE_URI')
        client = pymongo.MongoClient(host)
        db = client[db]
        self.coll = db[collection]

    def reset_db(self):
        self.coll.delete_many({})
        self.coll.insert_one({'id': 'current_habits', 'habits': DEFAULT_HABITS})
        self.coll.insert_one({'id': 'master_habit_list', 'habits': DEFAULT_HABITS})
        return list(self.coll.find({}))

    def get_default_habits(self):
        return DEFAULT_HABITS

    def get_current_habits(self):
        record = self.coll.find_one({'id': 'current_habits'}, {'_id': 0, 'habits': 1})
        habits = record['habits']
        return habits

    def get_master_habit_list(self):
        record = self.coll.find_one({'id': 'master_habit_list'}, {'_id': 0, 'habits': 1})
        habits = record['habits']
        return habits

    def get_habits_for_date(self, date: datetime.datetime):
        record = self.coll.find_one({'date': date}, {'_id': 0, 'habits': 1})
        return record['habits'] if record else None

    def delete_habit(self, habit: dict):
        name, value = habit.popitem()
        self.coll.update_one(
            {'id': 'current_habits'}, {'$unset': {f'habits.{name}': value}}
        )

    def add_habit(self, habit: dict):
        new_habit = habit.copy()
        name, value = new_habit.popitem()
        self.coll.update_one(
            {'id': 'current_habits'}, {'$set': {f'habits.{name}': value}}
        )

    def add_to_master_habit_list(self, habit: dict):
        new_habit = habit.copy()
        name, value = new_habit.popitem()
        self.coll.update_one(
            {'id': 'current_habits'}, {'$set': {f'habits.{name}': value}}
        )

    def record_daily_habits(self, date, habits):
        self.coll.update_one({'date': date}, {'$set': {'habits': habits}}, upsert=True)

    def append_habit_categories(self, habits):
        m = self.get_master_habit_list()
        return {
            k: {'checked': v, 'category': m.get(k).get('category')}
            for k, v in habits.items()
        }

    def get_aggregated_departments(self):
        return self.coll.aggregate(
            [{'$group': {'_id': '$department', 'emps': {'$sum': 1}}}]
        )


class JournalDBManager:
    def __init__(self):
        self.coll = None

    def init_app(self, app, db, collection):
        host = app.config.get('MONGODB_DATABASE_URI')
        client = pymongo.MongoClient(host)
        db = client[db]
        self.coll = db[collection]

    def create_text_index(self):
        self.coll.create_index([('entry', 'text')], name='entry')

    def reset_db(self):
        self.coll.delete_many({})

    def add_journal_entry(self, entry):
        self.coll.insert_one(entry)

    def search_entries(self, text):
        self.coll.find_one({"$text": {"$search": text}})

    def get_all_entries(self):
        return [entry for entry in self.coll.find({})]


class CountdownsDBManager:
    def __init__(self):
        self.coll = None

    def init_app(self, app, db, collection):
        host = app.config.get('MONGODB_DATABASE_URI')
        client = pymongo.MongoClient(host)
        db = client[db]
        self.coll = db[collection]

    @staticmethod
    def make_countdown_id_from_name(name):
        name = re.sub(r'[^a-zA-Z0-9]', '_', name)
        return f'{name.lower()}_days'

    @staticmethod
    def remove_time_from_dates(countdowns):
        fixed = [(name, date[:-9], name_id) for name, date, name_id in countdowns]
        return fixed

    def get_countdowns(self):
        countdowns = [cd for cd in self.coll.find({}, {'_id': 0}).sort('date', 1)]
        sorted_text_date_countdowns = [
            (
                c.get('name'),
                datetime.datetime.strftime(c.get('date'), '%B %d %Y %X'),
                c.get('name_id'),
            )
            for c in countdowns
        ]
        return sorted_text_date_countdowns
        # return countdowns

    def add_countdown(self, countdown):
        self.coll.insert_one(countdown)

    def delete_countdown(self, countdown):
        self.coll.delete_one(countdown)
