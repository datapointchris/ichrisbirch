-- Notes
-- tracks.events
-- tracks.todo
-- tracks.countdowns -> MongoDB
-- tracks.habits -> MongoDB
-- tracks.journal-> MongoDB

-- apartments.apartments
-- apartments.feature_types_mapping

-- moving.boxes
-- moving.items


-- TRACKS
create schema tracks;

	-- events
create table if not exists tracks.events (
	id integer primary key,
	name varchar(64) not null,
	date date not null,
	venue varchar(64) not null,
	url varchar(256),
	cost numeric not null,
	attending boolean not null,
	notes text
);



-- APARTMENTS
create schema apartments;

DROP TABLE IF EXISTS apartments.apartmentfeatures;
DROP TABLE IF EXISTS apartments.features;
DROP TABLE IF EXISTS apartments.apartments;


	-- apartments
CREATE TABLE IF NOT EXISTS apartments.apartments (
id serial PRIMARY KEY,
name TEXT,
address TEXT,
url TEXT,
notes TEXT
);


--features
CREATE TABLE IF NOT EXISTS apartments.features (
id serial PRIMARY KEY,
name TEXT,
weight real
)

-- apartmentfeatures
CREATE TABLE IF NOT EXISTS apartments.apartmentfeatures (
apartment_id integer REFERENCES apartments.apartments(id) ON DELETE cascade,
feature_id integer REFERENCES apartments.features(id) ON DELETE cascade,
value REAL,
PRIMARY KEY (apartment_id, feature_id)



INSERT INTO apartments.features(name, weight)
VALUES
('year', 7),
('rent', 1),
('sqft', 6),
('price_per', 6),
('pet_rent', 2),
('pet_deposit', 6),
('fees', 3),
('dishwasher', 9),
('washer_dryer', 9),
('countertops', 7),
('floor_level', 9),
('dog_walking', 4),
('dog_park', 7),
('groceries', 6),
('costco', 9),
('gym', 9),
('apt_gym', 7),
('quiet_ac', 8),
('ac_filter_can_change', 9),
('parking', 2),
('smart_thermostat', 8),
('electronic_lock', 4),
('trails', 5),
('bike_lanes', 5),
('to_work', 8),
('toll_road', 8),
('walk_in_closet', 5),
('ceiling_fans', 5),
('guest_parking', 8),
('speed_bumps', 2);
    

INSERT INTO apartments.apartments(name, address, url, notes)
VALUES
('Windsor Westbridge', '2300 Marsh Ln, Carrollton, TX 75006', 'https://www.apartments.com/windsor-westbridge-carrollton-tx/jmxtw14/', 'Notes'),
('16301 Ledgemont Ln', '16301 Ledgemont Ln, Addison, TX 75001', 'https://www.apartments.com/16301-ledgemont-ln-addison-tx/66e3ets/', 'Notes'),
('Bent Tree Trails', '16300 Ledgemenont Ln, Addison, TX 75001', 'https://www.apartments.com/bent-tree-trails-addison-tx/k8cf7s8/', 'Notes'),
('MAA Addison Circle', '5009 Addison Cir, Addison, TX 75001', 'https://www.apartments.com/maa-addison-circle-addison-tx/39b587f/', 'Notes'),
('Woods at Lakeshore', '3560 Country Square Dr, Carrollton, TX 75006', 'https://www.apartments.com/woods-at-lakeshore-carrollton-tx/bgc3k19/', 'Notes'),
('Lakehill Townhomes', '2610 Lakehill Ln, Carrollton, TX 75006', 'https://www.apartments.com/lakehill-townhomes-carrollton-tx/7nnr49y/', 'Notes'),
('Huntington Cove Townhomes', '14802 Enterprise Dr, Farmers Branch, TX 75234', 'https://www.apartments.com/huntington-cove-townhomes-farmers-branch-tx/lr2mtbd/', 'Notes'),
('Jade Addison', '3721 Spring Valley Rd, Addison, TX 75001', 'https://www.apartments.com/jade-addison-addison-tx/rb6wv72/', 'Notes');


INSERT INTO apartments.apartmentfeatures(value, apartment_id, feature_id)
VALUES
(1970, 1, 1),
(1978, 3, 1),
(1980, 5, 1),
(1500, 3, 2),
(1400, 1, 2),
(1800, 7, 2),
(700, 3, 3),
(880, 1, 3),
(1200, 6, 3);

SELECT 
  a.name AS apartment,
  a.id AS apartment_id,
  f.name AS feature, 
  f.id AS feature_id,
  f.weight, 
  af.value,
  avg(value) OVER() AS avg_value,
  value / (avg(value) OVER()) AS PERCENT,
  value / (avg(value) OVER()) * weight AS weighted
FROM apartments.apartments a
JOIN apartments.apartmentfeatures af
  ON a.id = af.apartment_id
JOIN apartments.features f
  ON f.id = af.feature_id
WHERE f.name = 'sqft';



-- insert new apartment with features
/*
name, address, url, notes, feature_name, value
 */
WITH apt_ids AS (
INSERT INTO apartments.apartments(name, address, url, notes)
VALUES
('Jade Addison', '3721 Spring Valley Rd, Addison, TX 75001', 'https://www.apartments.com/jade-addison-addison-tx/rb6wv72/', 'Notes')
RETURNING id AS apartment_id
)
INSERT INTO apartments.apartmentfeatures(apartment_id, feature_id, value)
SELECT apt_ids.apartment_id, f.id, value
FROM apt_ids, features f
WHERE f.name = feature_name

















-- MOVING

   -- boxes
create table if not exists boxes (
    id integer primary key not null,
    name text not null,
    size text not null,
    essential boolean default false,
    warm boolean default false,
    liquid boolean default false
);

	-- items
create table if not exists items (
    id integer primary key,
    box_id integer not null,
    name text,
    essential boolean default false,
    warm boolean default false,
    liquid boolean default false,
    foreign key (box_id) references boxes(id)
);

insert or ignore into boxes(id, name, size, essential, warm, liquid)
values
(1, 'Computers', 'medium', 0, 1, 0);

create VIRTUAL table if not exists search_items
	using FTS5(
    box_id UNINDEXED,
    name,
    essential UNINDEXED,
    warm UNINDEXED,
    liquid UNINDEXED,
    content = 'items',
    content_rowid = 'id'
);

create trigger if not exists item_insert after insert on
items
    begin
        insert into search_items (rowid, name)
values (new.id, new.name);

end;

create trigger if not exists item_delete after delete on
items
    begin
        insert into search_items (search_items, rowid, name)
values ('delete', old.id, old.name);

end;

create trigger if not exists item_update after update on
items
    begin
        insert into search_items (search_items, rowid, name)
values ('delete', old.id, old.name);

insert into search_items (rowid, name)
values (new.id, new.name);

end;
   
   
   
   
   
   
   