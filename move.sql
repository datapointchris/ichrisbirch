PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE boxes (
    id integer PRIMARY KEY NOT NULL,
    name TEXT NOT NULL,
    size TEXT NOT NULL,
    essential boolean DEFAULT FALSE,
    warm boolean DEFAULT FALSE,
    liquid boolean DEFAULT FALSE
);
INSERT INTO boxes VALUES(1,'Computers','medium',0,1,0);
INSERT INTO boxes VALUES(2,'Bathroom','small',1,1,1);
INSERT INTO boxes VALUES(3,'Bathroom 2','kcup',1,1,1);
INSERT INTO boxes VALUES(4,'Pills','xsmall',1,1,1);
INSERT INTO boxes VALUES(5,'Food - Turquoise','bag',0,0,1);
INSERT INTO boxes VALUES(6,'Monitors and Clock','xlarge',1,1,0);
INSERT INTO boxes VALUES(7,'Essential Electronics','kcup',1,1,0);
INSERT INTO boxes VALUES(8,'Shoes - Purple','bag',0,0,0);
INSERT INTO boxes VALUES(9,'Misc Room','small',0,0,0);
INSERT INTO boxes VALUES(10,'Misc Everything','xsmall',0,0,0);
INSERT INTO boxes VALUES(11,'Socks Underwear - Popsicle','bag',1,0,0);
INSERT INTO boxes VALUES(12,'Shorts Tanktops Pants - Popsicle','bag',1,0,0);
INSERT INTO boxes VALUES(13,'Misc Clothes - Turquoise','bag',0,0,0);
INSERT INTO boxes VALUES(14,'Exercise Equipment - Green','bag',0,0,0);
INSERT INTO boxes VALUES(15,'K Cups - Turquoise','bag',0,0,0);
INSERT INTO boxes VALUES(16,'Food Staples - Turquoise','bag',0,0,1);
INSERT INTO boxes VALUES(17,'Vacuum Curtains - Gray','bag',0,0,0);
INSERT INTO boxes VALUES(18,'Garbage Cans - Turquoise','bag',0,0,0);
INSERT INTO boxes VALUES(19,'Gloving Shorts Socks - Turquoise','bag',0,0,0);
CREATE TABLE items (
    id integer PRIMARY KEY,
    box_id integer NOT NULL,
    name TEXT,
    essential boolean DEFAULT FALSE,
    warm boolean DEFAULT FALSE,
    liquid boolean DEFAULT FALSE,
    FOREIGN KEY (box_id) REFERENCES boxes(id)
);
INSERT INTO items VALUES(1,1,'Linux Box',0,1,0);
INSERT INTO items VALUES(2,1,'Battery backup',0,1,0);
INSERT INTO items VALUES(3,2,'Blue Bathroom Bin',1,0,0);
INSERT INTO items VALUES(4,2,'Orange Wash',0,1,1);
INSERT INTO items VALUES(5,3,'Rubbing alcohol',0,0,1);
INSERT INTO items VALUES(6,3,'Hair clippers',0,0,0);
INSERT INTO items VALUES(7,3,'Cologne',0,1,1);
INSERT INTO items VALUES(8,3,'Essential oils',0,1,1);
INSERT INTO items VALUES(9,2,'Boxer briefs',0,0,0);
INSERT INTO items VALUES(14,5,'Green powder',0,0,0);
INSERT INTO items VALUES(16,5,'MCT oil',0,0,1);
INSERT INTO items VALUES(17,5,'Oil jars',0,0,1);
INSERT INTO items VALUES(18,6,'Monitors',0,1,0);
INSERT INTO items VALUES(19,6,'clock',0,0,0);
INSERT INTO items VALUES(20,6,'Keyboard',0,0,0);
INSERT INTO items VALUES(24,7,'Monitor cords',0,0,0);
INSERT INTO items VALUES(25,7,'Mac mini',0,0,0);
INSERT INTO items VALUES(26,7,'alexa',0,0,0);
INSERT INTO items VALUES(27,7,'webcam',0,0,0);
INSERT INTO items VALUES(28,7,'monitor cables',0,0,0);
INSERT INTO items VALUES(29,9,'Strip lights',0,0,0);
INSERT INTO items VALUES(30,9,'Bear tent',0,0,0);
INSERT INTO items VALUES(31,9,'Yellow tablets',0,0,0);
INSERT INTO items VALUES(32,9,'Extra cables',0,0,0);
INSERT INTO items VALUES(33,9,'Bong',0,0,0);
INSERT INTO items VALUES(34,10,'lamp',0,0,0);
INSERT INTO items VALUES(35,10,'electric toothbrush',0,0,0);
INSERT INTO items VALUES(36,10,'black power strips',0,0,0);
INSERT INTO items VALUES(37,10,'oil diffuser',0,0,0);
INSERT INTO items VALUES(38,1,'Linux box',0,0,0);
INSERT INTO items VALUES(39,1,'Battery backup',0,0,0);
INSERT INTO items VALUES(40,1,'Small battery backup',0,0,0);
INSERT INTO items VALUES(41,1,'Heater',0,0,0);
INSERT INTO items VALUES(42,11,'Masks',0,0,0);
INSERT INTO items VALUES(43,11,'Warm socks',0,0,0);
INSERT INTO items VALUES(44,11,'Slippers',0,0,0);
INSERT INTO items VALUES(47,13,'biking shorts',0,0,0);
INSERT INTO items VALUES(48,6,'Grey blanket',0,0,0);
INSERT INTO items VALUES(49,6,'Sit pillows',0,0,0);
INSERT INTO items VALUES(50,6,'Bed pillow',0,0,0);
INSERT INTO items VALUES(52,14,'trx straps',0,0,0);
INSERT INTO items VALUES(53,14,'yoga blocks',0,0,0);
INSERT INTO items VALUES(54,14,'exercise bands',0,0,0);
INSERT INTO items VALUES(55,5,'K cup tree',0,0,0);
INSERT INTO items VALUES(56,18,'Garbage cans',0,0,0);
INSERT INTO items VALUES(57,18,'K Cups',0,0,0);
INSERT INTO items VALUES(58,18,'Light strip on pink blender bottle',0,0,0);
INSERT INTO items VALUES(59,18,'protein',0,0,0);
INSERT INTO items VALUES(60,18,'rice',0,0,0);
INSERT INTO items VALUES(61,18,'spices',0,0,0);
INSERT INTO items VALUES(62,19,'Gloves',0,0,0);
INSERT INTO items VALUES(63,19,'Workout shorts',0,0,0);
INSERT INTO items VALUES(64,19,'Socks',0,0,0);
INSERT INTO items VALUES(65,19,'Slippers',0,0,0);
INSERT INTO items VALUES(66,13,'long sleeve shirts',0,0,0);
PRAGMA writable_schema=ON;
INSERT INTO sqlite_schema(type,name,tbl_name,rootpage,sql)VALUES('table','search_items','search_items',0,'CREATE VIRTUAL TABLE search_items USING FTS5(
    box_id UNINDEXED,
    name,
    essential UNINDEXED,
    warm UNINDEXED,
    liquid UNINDEXED,
    content=''items'',
    content_rowid=''id''
)');
CREATE TABLE IF NOT EXISTS 'search_items_data'(id INTEGER PRIMARY KEY, block BLOB);
INSERT INTO search_items_data VALUES(1,X'370066000000');
INSERT INTO search_items_data VALUES(10,X'0000000002055300051101010101010201010301010401010000');
INSERT INTO search_items_data VALUES(137438953473,X'000000150730676c6f7665732d010503696e672d01040a');
INSERT INTO search_items_data VALUES(274877906945,X'0000000f0830676f67676c65732e0104');
INSERT INTO search_items_data VALUES(412316860417,X'0000002805306c6f6e6742060101020106736869727473420601010402056c656576654206010103040b0d');
INSERT INTO search_items_data VALUES(549755813889,X'0000001f05306c6f6e6733010106736869727473330102056c65657665330104080a');
INSERT INTO search_items_data VALUES(2336462209025,X'000004230830616c636f686f6c050601010303036578611a0601010201066261636b757002060101032506010103010601010403036e6473360601010303067468726f6f6d030601010304047465727902060101022506010102010601010302036561721e0601010203016432060101020205696b696e672f0601010203016e030601010402046c61636b240601010204046e6b657430060101030305656e6465723a0601010603046f636b73350601010303027565030601010202036f6e672106010102030474746c653a060101070301780106010103250601010304026572090601010202057269656673090601010301066361626c65731c06010103040601010303026e73380601010302076c697070657273060601010303036f636b130601010202066f6c6f676e6507060101020303726473180601010302027570370601010304017339060101030108646966667573657225060101030108656c656374726963230601010202087373656e7469616c0806010102020778657263697365360601010203037472612006010102010767617262616765380601010202056c6f7665732d0601010311060101020503696e672d0601010202066f67676c65732e0601010202047265656e0e060101020401793006010102010468616972060601010202056561746572290601010201046a617273110601010301016b3706010102020601010202076579626f617264140601010201046c616d7022060101020204696768743a060101020601731d0601010303036e75780106010102250601010202036f6e67330601010201036d616319060101020303736b732a060101020202637410060101020203696e69190601010302066f6e69746f7218060101020406010102080173120601010201036f696c100601010301060101021406010102040173080601010302016e3a06010104020572616e67650406010102010670696c6c6f773206010103070173310601010303026e6b3a0601010502056f776465720e060101030402657224060101030206726f7465696e3b060101020104726963653c060101020206756262696e6705060101020106736869727473330601010403046f7274732f06010103100601010302026974310601010202056c65657665330601010303066970706572732c06010102150601010202046d616c6c280601010202046f636b732b060101031506010102020570696365733d06010102020574726170733406010103040269701d060101021d06010103060173240601010401077461626c6574731f060101030203656e741e0601010302096f6f74686272757368230601010302037265653706010104030178340601010201047761726d2b060101020302736804060101030205656263616d1b0601010202066f726b6f75743f06010102010679656c6c6f771f0601010202036f67613506010102040e0a170a0d150a080c080b0b0c0b090a0b0d090c12090e0a0d0a09080f0f0f0e0a0e110a0d0b080b0c0b0d0e0b0b080f0a0a0a090a12081408080c0d08090c090d0b0d0d10090c120b100c0c0e080e0a100a080b090c0d0d');
CREATE TABLE IF NOT EXISTS 'search_items_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
INSERT INTO search_items_idx VALUES(1,X'',2);
INSERT INTO search_items_idx VALUES(2,X'',2);
INSERT INTO search_items_idx VALUES(3,X'',2);
INSERT INTO search_items_idx VALUES(4,X'',2);
INSERT INTO search_items_idx VALUES(17,X'',2);
CREATE TABLE IF NOT EXISTS 'search_items_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
INSERT INTO search_items_docsize VALUES(1,X'0002000000');
INSERT INTO search_items_docsize VALUES(2,X'0002000000');
INSERT INTO search_items_docsize VALUES(3,X'0003000000');
INSERT INTO search_items_docsize VALUES(4,X'0002000000');
INSERT INTO search_items_docsize VALUES(5,X'0002000000');
INSERT INTO search_items_docsize VALUES(6,X'0002000000');
INSERT INTO search_items_docsize VALUES(7,X'0001000000');
INSERT INTO search_items_docsize VALUES(8,X'0002000000');
INSERT INTO search_items_docsize VALUES(9,X'0002000000');
INSERT INTO search_items_docsize VALUES(14,X'0002000000');
INSERT INTO search_items_docsize VALUES(16,X'0002000000');
INSERT INTO search_items_docsize VALUES(17,X'0002000000');
INSERT INTO search_items_docsize VALUES(18,X'0001000000');
INSERT INTO search_items_docsize VALUES(19,X'0001000000');
INSERT INTO search_items_docsize VALUES(20,X'0001000000');
INSERT INTO search_items_docsize VALUES(24,X'0002000000');
INSERT INTO search_items_docsize VALUES(25,X'0002000000');
INSERT INTO search_items_docsize VALUES(26,X'0001000000');
INSERT INTO search_items_docsize VALUES(27,X'0001000000');
INSERT INTO search_items_docsize VALUES(28,X'0002000000');
INSERT INTO search_items_docsize VALUES(29,X'0002000000');
INSERT INTO search_items_docsize VALUES(30,X'0002000000');
INSERT INTO search_items_docsize VALUES(31,X'0002000000');
INSERT INTO search_items_docsize VALUES(32,X'0002000000');
INSERT INTO search_items_docsize VALUES(33,X'0001000000');
INSERT INTO search_items_docsize VALUES(34,X'0001000000');
INSERT INTO search_items_docsize VALUES(35,X'0002000000');
INSERT INTO search_items_docsize VALUES(36,X'0003000000');
INSERT INTO search_items_docsize VALUES(37,X'0002000000');
INSERT INTO search_items_docsize VALUES(38,X'0002000000');
INSERT INTO search_items_docsize VALUES(39,X'0002000000');
INSERT INTO search_items_docsize VALUES(40,X'0003000000');
INSERT INTO search_items_docsize VALUES(41,X'0001000000');
INSERT INTO search_items_docsize VALUES(42,X'0001000000');
INSERT INTO search_items_docsize VALUES(43,X'0002000000');
INSERT INTO search_items_docsize VALUES(44,X'0001000000');
INSERT INTO search_items_docsize VALUES(47,X'0002000000');
INSERT INTO search_items_docsize VALUES(48,X'0002000000');
INSERT INTO search_items_docsize VALUES(49,X'0002000000');
INSERT INTO search_items_docsize VALUES(50,X'0002000000');
INSERT INTO search_items_docsize VALUES(52,X'0002000000');
INSERT INTO search_items_docsize VALUES(53,X'0002000000');
INSERT INTO search_items_docsize VALUES(54,X'0002000000');
INSERT INTO search_items_docsize VALUES(55,X'0003000000');
INSERT INTO search_items_docsize VALUES(56,X'0002000000');
INSERT INTO search_items_docsize VALUES(57,X'0002000000');
INSERT INTO search_items_docsize VALUES(58,X'0006000000');
INSERT INTO search_items_docsize VALUES(59,X'0001000000');
INSERT INTO search_items_docsize VALUES(60,X'0001000000');
INSERT INTO search_items_docsize VALUES(61,X'0001000000');
INSERT INTO search_items_docsize VALUES(62,X'0001000000');
INSERT INTO search_items_docsize VALUES(63,X'0002000000');
INSERT INTO search_items_docsize VALUES(64,X'0001000000');
INSERT INTO search_items_docsize VALUES(65,X'0001000000');
INSERT INTO search_items_docsize VALUES(66,X'0003000000');
CREATE TABLE IF NOT EXISTS 'search_items_config'(k PRIMARY KEY, v) WITHOUT ROWID;
INSERT INTO search_items_config VALUES('version',4);
CREATE TRIGGER item_insert AFTER INSERT ON items
    BEGIN
        INSERT INTO search_items (rowid, name)
        VALUES (new.id, new.name);
    END;
CREATE TRIGGER item_delete AFTER DELETE ON items
    BEGIN
        INSERT INTO search_items (search_items, rowid, name)
        VALUES ('delete', old.id, old.name);
    END;
CREATE TRIGGER item_update AFTER UPDATE ON items
    BEGIN
        INSERT INTO search_items (search_items, rowid, name)
        VALUES ('delete', old.id, old.name);
        INSERT INTO search_items (rowid, name)
        VALUES (new.id, new.name);
    END;
PRAGMA writable_schema=OFF;
COMMIT;
.auth ON|OFF             Show authorizer callbacks
.backup ?DB? FILE        Backup DB (default "main") to FILE
.bail on|off             Stop after hitting an error.  Default OFF
.binary on|off           Turn binary output on or off.  Default OFF
.cd DIRECTORY            Change the working directory to DIRECTORY
.changes on|off          Show number of rows changed by SQL
.check GLOB              Fail if output since .testcase does not match
.clone NEWDB             Clone data into NEWDB from the existing database
.databases               List names and files of attached databases
.dbconfig ?op? ?val?     List or change sqlite3_db_config() options
.dbinfo ?DB?             Show status information about the database
.dump ?OBJECTS?          Render database content as SQL
.echo on|off             Turn command echo on or off
.eqp on|off|full|...     Enable or disable automatic EXPLAIN QUERY PLAN
.excel                   Display the output of next command in spreadsheet
.exit ?CODE?             Exit this program with return-code CODE
.expert                  EXPERIMENTAL. Suggest indexes for queries
.explain ?on|off|auto?   Change the EXPLAIN formatting mode.  Default: auto
.filectrl CMD ...        Run various sqlite3_file_control() operations
.fullschema ?--indent?   Show schema and the content of sqlite_stat tables
.headers on|off          Turn display of headers on or off
.help ?-all? ?PATTERN?   Show help text for PATTERN
.import FILE TABLE       Import data from FILE into TABLE
.imposter INDEX TABLE    Create imposter table TABLE on index INDEX
.indexes ?TABLE?         Show names of indexes
.limit ?LIMIT? ?VAL?     Display or change the value of an SQLITE_LIMIT
.lint OPTIONS            Report potential schema issues.
.log FILE|off            Turn logging on or off.  FILE can be stderr/stdout
.mode MODE ?TABLE?       Set output mode
.nullvalue STRING        Use STRING in place of NULL values
.once ?OPTIONS? ?FILE?   Output for the next SQL command only to FILE
.open ?OPTIONS? ?FILE?   Close existing database and reopen FILE
.output ?FILE?           Send output to FILE or stdout if FILE is omitted
.parameter CMD ...       Manage SQL parameter bindings
.print STRING...         Print literal STRING
.progress N              Invoke progress handler after every N opcodes
.prompt MAIN CONTINUE    Replace the standard prompts
.quit                    Exit this program
.read FILE               Read input from FILE
.recover                 Recover as much data as possible from corrupt db.
.restore ?DB? FILE       Restore content of DB (default "main") from FILE
.save FILE               Write in-memory database into FILE
.scanstats on|off        Turn sqlite3_stmt_scanstatus() metrics on or off
.schema ?PATTERN?        Show the CREATE statements matching PATTERN
.selftest ?OPTIONS?      Run tests defined in the SELFTEST table
.separator COL ?ROW?     Change the column and row separators
.session ?NAME? CMD ...  Create or control sessions
.sha3sum ...             Compute a SHA3 hash of database content
.shell CMD ARGS...       Run CMD ARGS... in a system shell
.show                    Show the current values for various settings
.stats ?ARG?             Show stats or turn stats on or off
.system CMD ARGS...      Run CMD ARGS... in a system shell
.tables ?TABLE?          List names of tables matching LIKE pattern TABLE
.testcase NAME           Begin redirecting output to 'testcase-out.txt'
.testctrl CMD ...        Run various sqlite3_test_control() operations
.timeout MS              Try opening locked tables for MS milliseconds
.timer on|off            Turn SQL timer on or off
.trace ?OPTIONS?         Output each SQL statement as it is run
.vfsinfo ?AUX?           Information about the top-level VFS
.vfslist                 List all available VFSes
.vfsname ?AUX?           Print the name of the VFS stack
.width NUM1 NUM2 ...     Set minimum column widths for columnar output
