PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE apartments (
id integer primary key not null,
name text,
address text,
url text,
year integer,
rent integer,
sqft integer,
price_per integer,
pet_rent integer,
pet_deposit integer,
fees integer,
dishwasher boolean,
washer_dryer text,
countertops text,
floor_level integer,
dog_walking integer,
dog_park boolean,
groceries integer,
costco integer,
gym integer,
apt_gym integer,
quiet_ac boolean,
ac_filter_can_change boolean,
parking integer,
smart_thermostat boolean,
electronic_lock boolean,
trails integer,
bike_lanes integer,
to_work integer,
toll_road boolean,
walk_in_closet boolean,
ceiling_fans boolean,
guest_parking integer,
speed_bumps boolean,
notes text
, Wide Bathroom Counter boolean, Big Bathroom Counter boolean);
INSERT INTO apartments VALUES(2,'Roehampton','18333 Roehampton Dr, Dallas, TX 75252','https://www.apartments.com/18333-roehampton-dr-dallas-tx-unit-721/1dzbbt6/',NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(3,'Thornbury at Chase Oaks','7101 Chase Oaks Blvd, Plano, TX 75025','https://www.apartments.com/thornbury-at-chase-oaks-plano-tx/v8x64zf/',NULL,NULL,NULL,0,20,400,175,1,'hookup',NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(4,'Villas at Legacy','5301 W Spring Creek Pky, Plano, TX 75024','https://www.apartments.com/villas-at-legacy-plano-tx/k3bpecc/',NULL,NULL,NULL,0,30,700,175,1,'hookup','granite',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(5,'Auberry at Twin Creeks','705 Bray Central Dr, Allen, TX 75013','https://www.apartments.com/auberry-at-twin-creeks-allen-tx/t1kq6eb/',NULL,NULL,NULL,0,20,400,200,1,'unit','granite',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(6,'Essence at North Dallas','4200 Horizon North Pky, Dallas, TX 78287','https://www.apartments.com/essence-at-north-dallas-dallas-tx/3z14q8g/',NULL,NULL,NULL,0,20,200,175,1,'hookup, unit','granite',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(7,'Andalusian Gate','3653 Briargrove Ln, Dallas, TX 75287','https://www.apartments.com/andalusian-gate-dallas-tx/bb1hytc/',NULL,NULL,NULL,0,10,500,150,1,'hookup','granite',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,1,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(8,'Ashwood Park','7650 McCallum Bldv, Dallas, TX 75252','https://www.apartments.com/ashwood-park-apartments-dallas-tx/1rby186/',NULL,NULL,NULL,0,0,300,50,1,'hookup',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(9,'Stonebrook Village','7500 Rolling Brook Dr, Frisco, TX 75034','https://www.apartments.com/stonebrook-village-apts-frisco-tx/yke66lt/',NULL,NULL,NULL,0,0,575,35,NULL,'unit, hookup',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(10,'Mason','1300 Eldorado Pky, McKinney, TX 75069','https://www.apartments.com/mason-mckinney-tx/zsj02vy/',NULL,1637,1090,1.5,10,500,210,1,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(11,'Hunter''s Hill','18081 Midway Rd, Dallas, TX 75287','https://www.apartments.com/hunters-hill-dallas-tx/6v07n0r/',NULL,NULL,NULL,NULL,10,150,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(12,'Bella Vist Apartment Homes','1834 E Peters Colony Rd, Carrollton, TX 75007','https://www.apartments.com/bella-vista-apartment-homes-carrollton-tx/vc0x8gd/',1982,NULL,NULL,NULL,25,500,500,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(13,'Edentree','1721 Frakford Rd, Carrollton, TX 75007','https://www.apartments.com/edentree-carrollton-tx/x5gbjkn/',1983,NULL,NULL,NULL,10,400,195,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(14,'State Apartments Dallas','18050 Kelly Blvd, Dallas, TX 75287','https://www.apartments.com/slate-apartments-dallas-dallas-tx/e0tgg4q/',1985,NULL,NULL,NULL,10,300,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(15,'Plano Park Townhomes','2253 Ashley Park Dr, Plano, TX 75074','https://www.apartments.com/plano-park-townhomes-plano-tx/0jt0xl1/',1984,NULL,NULL,NULL,20,400,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(16,'Independence Crossing','6501 Independence Pky, Plano, TX 75023','https://www.apartments.com/independence-crossing-plano-tx/snbgy36/',1999,NULL,NULL,NULL,25,400,145,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(17,'Wade Crossing Apartment Homes','9399 Wade Blvd, Frisco, TX 75035','https://www.apartments.com/wade-crossing-apartment-homes-frisco-tx/hzzbye0/',2000,NULL,NULL,NULL,20,500,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(18,'Cobb Hill Apartments','6000 Eldorado Pky, Frisco, TX 75033','https://www.apartments.com/cobb-hill-apartments-frisco-tx/55xss2q/',2008,NULL,NULL,NULL,15,350,200,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(19,'Galleria Townhomes','1737 E Frankford Rd, Carrollton, TX 75007','https://www.apartments.com/galleria-townhomes-carrollton-tx/tyvgwhb/',1983,NULL,NULL,NULL,0,400,165,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(20,'Stonegate','2521 Wolford St, McKinney, TX 75071','https://www.apartments.com/stonegate-mckinney-tx/k99c8eb/',1983,NULL,NULL,NULL,10,300,220,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(21,'Amber Vista Apartments','1901 E 15th St, Plano, TX 75074','https://www.apartments.com/amber-vista-apartments-plano-tx/96jdbq7/',1974,NULL,NULL,NULL,25,300,565,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(22,'Greenbriar Apartments','1901 W Spring Creek Pky, Plano, TX 75023','https://www.apartments.com/greenbriar-apartments-plano-tx/8wn7ey0/',1983,NULL,NULL,NULL,0,400,150,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(23,'Crossings on Marsh','18788 Marsh Ln, Dallas, TX 75287','https://www.apartments.com/crossings-on-marsh-dallas-tx/w9lrd9h/',1985,NULL,NULL,NULL,10,300,230,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(24,'Mission Eagle Pointe','325 S Jupiter Rd, Allen, TX 75002','https://www.apartments.com/mission-eagle-pointe-allen-tx/g2yd2bx/',2004,NULL,NULL,NULL,40,700,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(25,'Custer Park Apartments','3400 Custer Rd, Plano, TX 75023','https://www.apartments.com/custer-park-apartments-plano-tx/zqrwvdy/',1978,NULL,NULL,NULL,0,400,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(26,'Villages at Clear Spring','2600 Clear Springs Dr, Richardson, TX 75082','https://www.apartments.com/villages-at-clear-springs-richardson-tx/05emf82/',1998,NULL,NULL,NULL,15,400,580,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(27,'Cross Creek','7401 Alma Dr, Plano, TX 75025','https://www.apartments.com/cross-creek-plano-tx/hdmgh21/',1983,NULL,NULL,NULL,20,300,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(28,'The Brook','7549 Stonebrook Pky, Frisco, TX 75034','https://www.apartments.com/the-brook-frisco-tx/k883wy9/',1999,NULL,NULL,NULL,0,400,200,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(29,'Champions of North Dallas','4912 Haverwood Ln, Dallas, TX 75287','https://www.apartments.com/champions-of-north-dallas-dallas-tx/0n8e863/',1986,NULL,NULL,NULL,0,300,125,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(30,'The Point at Deerfield Apartments','4640 Hedgcoxe Rd, Plano, TX 75024','https://www.apartments.com/the-point-at-deerfield-apartments-plano-tx/54ggmvq/',1999,NULL,NULL,NULL,15,500,165,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(31,'The Manhattan Apartments','18331 Roehampton Dr, Dallas, TX 75252','https://www.apartments.com/the-manhattan-apartments-dallas-tx/wsmpr5k/',1983,NULL,NULL,NULL,10,200,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(32,'Indian Creek','3910 Old Denton Rd, Carrollton, TX 75007','https://www.apartments.com/indian-creek-carrollton-tx/qffc75y/',1985,NULL,NULL,NULL,0,0,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(33,'Timberglen Apartments','3773 Timberglen Rd, Dallas, TX 75287','https://www.apartments.com/timberglen-apartments-dallas-tx/9phrrq5/',1984,NULL,NULL,NULL,0,0,100,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(34,'Waterford at the Park','3640 Old Denton Rd, Carrollton, TX 75007','https://www.apartments.com/waterford-at-the-park-carrollton-tx/cp7vjrf/',1985,NULL,NULL,NULL,0,600,115,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
INSERT INTO apartments VALUES(35,'Pear Ridge','4753 Old Bent Tree Ln, Dallas, TX 75287','https://www.apartments.com/pear-ridge-dallas-tx/2d7clxc/',1986,NULL,NULL,NULL,20,500,175,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
CREATE TABLE feature_types_mapping (
id integer primary key not null,
name text,
type text);
INSERT INTO feature_types_mapping VALUES(1,'id','integer');
INSERT INTO feature_types_mapping VALUES(2,'name','text');
INSERT INTO feature_types_mapping VALUES(3,'address','text');
INSERT INTO feature_types_mapping VALUES(4,'url','text');
INSERT INTO feature_types_mapping VALUES(5,'year','integer');
INSERT INTO feature_types_mapping VALUES(6,'rent','integer');
INSERT INTO feature_types_mapping VALUES(7,'sqft','integer');
INSERT INTO feature_types_mapping VALUES(8,'price_per','integer');
INSERT INTO feature_types_mapping VALUES(9,'pet_rent','integer');
INSERT INTO feature_types_mapping VALUES(10,'pet_deposit','integer');
INSERT INTO feature_types_mapping VALUES(11,'fees','integer');
INSERT INTO feature_types_mapping VALUES(12,'dishwasher','boolean');
INSERT INTO feature_types_mapping VALUES(13,'washer_dryer','text');
INSERT INTO feature_types_mapping VALUES(14,'countertops','text');
INSERT INTO feature_types_mapping VALUES(15,'floor_level','integer');
INSERT INTO feature_types_mapping VALUES(16,'dog_walking','integer');
INSERT INTO feature_types_mapping VALUES(17,'dog_park','boolean');
INSERT INTO feature_types_mapping VALUES(18,'groceries','integer');
INSERT INTO feature_types_mapping VALUES(19,'costco','integer');
INSERT INTO feature_types_mapping VALUES(20,'gym','integer');
INSERT INTO feature_types_mapping VALUES(21,'apt_gym','integer');
INSERT INTO feature_types_mapping VALUES(22,'quiet_ac','boolean');
INSERT INTO feature_types_mapping VALUES(23,'ac_filter_can_change','boolean');
INSERT INTO feature_types_mapping VALUES(24,'parking','integer');
INSERT INTO feature_types_mapping VALUES(25,'smart_thermostat','boolean');
INSERT INTO feature_types_mapping VALUES(26,'electronic_lock','boolean');
INSERT INTO feature_types_mapping VALUES(27,'trails','integer');
INSERT INTO feature_types_mapping VALUES(28,'bike_lanes','integer');
INSERT INTO feature_types_mapping VALUES(29,'to_work','integer');
INSERT INTO feature_types_mapping VALUES(30,'toll_road','boolean');
INSERT INTO feature_types_mapping VALUES(31,'walk_in_closet','boolean');
INSERT INTO feature_types_mapping VALUES(32,'ceiling_fans','boolean');
INSERT INTO feature_types_mapping VALUES(33,'guest_parking','integer');
INSERT INTO feature_types_mapping VALUES(34,'speed_bumps','boolean');
INSERT INTO feature_types_mapping VALUES(35,'notes','text');
INSERT INTO feature_types_mapping VALUES(36,'Wide Bathroom Counter','boolean');
INSERT INTO feature_types_mapping VALUES(37,'Big Bathroom Counter','boolean');
COMMIT;