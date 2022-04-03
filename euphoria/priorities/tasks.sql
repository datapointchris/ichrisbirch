DROP TABLE IF EXISTS tasks;

CREATE TABLE IF NOT EXISTS tasks(
    id serial PRIMARY KEY,
    name TEXT,
    category TEXT,
    subcategory1 TEXT,
    subcategory2 TEXT,
    priority integer,
    add_date timestamp WITH TIME ZONE,
    complete_date timestamp WITH TIME ZONE
);

INSERT INTO
    tasks(name, category, priority, add_date)
VALUES
    ('task1', 'computer', 10, CURRENT_TIMESTAMP),
    ('task2', 'computer', 15, CURRENT_TIMESTAMP),
    ('task3', 'computer', 8, CURRENT_TIMESTAMP),
    ('task4', 'chore', 100, CURRENT_TIMESTAMP),
    ('task5', 'chore', 40, CURRENT_TIMESTAMP),
    ('task6', 'chore', 13, CURRENT_TIMESTAMP),
    ('task7', 'computer', 35, CURRENT_TIMESTAMP),
    ('task8', 'computer', 48, CURRENT_TIMESTAMP),
    ('task9', 'computer', 0, CURRENT_TIMESTAMP),
    ('task10', 'work', 1, CURRENT_TIMESTAMP);