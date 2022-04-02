PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "tracks.events" (
	id INTEGER NOT NULL, 
	name VARCHAR(64) NOT NULL, 
	date DATETIME NOT NULL, 
	venue VARCHAR(64) NOT NULL, 
	url VARCHAR(256), 
	cost FLOAT NOT NULL, 
	attending BOOLEAN NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id)
);
INSERT INTO "tracks.events" VALUES(1,'Le Youth','2022-03-10 00:00:00.000000','venu','url',20.0,0,'thurs');
COMMIT;
