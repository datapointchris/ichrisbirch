create table if not exists apartments (
id integer primary key not null,
name text,
address text,
url text);

create table if not exists features (
id integer primary key not null,
name text unique,
type text);

insert or ignore into features(name, type)
VALUES
    ('year', 'integer'),
    ('rent', 'integer'),
    ('sqft', 'integer'),
    ('price_per', 'integer'),
    ('pet_rent', 'integer'),
    ('pet_deposit', 'integer'),
    ('fees', 'integer'),
    ('dishwasher', 'boolean'),
    ('washer_dryer', 'text'),
    ('countertops', 'text'),
    ('floor_level', 'integer'),
    ('dog_walking', 'integer'),
    ('dog_park', 'boolean'),
    ('groceries', 'integer'),
    ('costco', 'integer'),
    ('gym', 'integer'),
    ('apt_gym', 'integer'),
    ('quiet_ac', 'boolean'),
    ('ac_filter_can_change', 'boolean'),
    ('parking', 'integer'),
    ('smart_thermostat', 'boolean'),
    ('electronic_lock', 'boolean'),
    ('trails', 'integer'),
    ('bike_lanes', 'integer'),
    ('to_work', 'integer'),
    ('toll_road', 'boolean'),
    ('walk_in_closet', 'boolean'),
    ('ceiling_fans', 'boolean'),
    ('guest_parking', 'integer'),
    ('speed_bumps', 'boolean'),
    ('notes', 'text');

create table if not exists apartment_features (
apt_id,
feature_id,
feature_value
);


