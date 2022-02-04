-- sqlite

DROP table if exists boxes;

DROP table if exists items;

DROP table if exists search_items;

DROP trigger if exists item_insert;

DROP trigger if exists item_delete;

DROP trigger if exists item_update;

CREATE TABLE IF NOT EXISTS boxes (
    id integer PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    size TEXT NOT NULL,
    essential boolean DEFAULT FALSE,
    warm boolean DEFAULT FALSE,
    liquid boolean DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS items (
    id integer PRIMARY KEY,
    box_id integer NOT NULL,
    name TEXT,
    essential boolean DEFAULT FALSE,
    warm boolean DEFAULT FALSE,
    liquid boolean DEFAULT FALSE,
    FOREIGN KEY (box_id) REFERENCES boxes(id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_items USING FTS5(
    box_id UNINDEXED,
    name,
    essential UNINDEXED,
    warm UNINDEXED,
    liquid UNINDEXED,
    content='items',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS item_insert AFTER INSERT ON items
    BEGIN
        INSERT INTO search_items (rowid, name)
        VALUES (new.id, new.name);
    END;

CREATE TRIGGER IF NOT EXISTS item_delete AFTER DELETE ON items
    BEGIN
        INSERT INTO search_items (search_items, rowid, name)
        VALUES ('delete', old.id, old.name);
    END;

CREATE TRIGGER IF NOT EXISTS item_update AFTER UPDATE ON items
    BEGIN
        INSERT INTO search_items (search_items, rowid, name)
        VALUES ('delete', old.id, old.name);
        INSERT INTO search_items (rowid, name)
        VALUES (new.id, new.name);
    END;