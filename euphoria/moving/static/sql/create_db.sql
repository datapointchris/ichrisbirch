-- sqlite

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

INSERT OR IGNORE INTO boxes(id, name, size, essential, warm, liquid)
VALUES
(1, 'Computers', 'medium', 0, 1, 0);

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