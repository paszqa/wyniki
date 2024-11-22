# Gov vote results

Script generates a website from Polish government site that lists vote results.


# How to run it:
1. Prepare a database and create a table "sejm" within, here's CREATE code for it:

```
CREATE TABLE `sejm` (
	`id` INT(11) NOT NULL AUTO_INCREMENT,
	`nrPos` INT(11) NULL DEFAULT NULL,
	`date` DATE NULL DEFAULT NULL,
	`nrGlos` INT(11) NULL DEFAULT NULL,
	`godz` VARCHAR(30) NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
	`temat` TEXT NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
	`partia` VARCHAR(50) NULL DEFAULT NULL COLLATE 'utf8mb4_general_ci',
	`czlonkowie` INT(11) NULL DEFAULT NULL,
	`za` INT(11) NULL DEFAULT NULL,
	`przeciw` INT(11) NULL DEFAULT NULL,
	`wstrzymal` INT(11) NULL DEFAULT NULL,
	`nieobecni` INT(11) NULL DEFAULT NULL,
	PRIMARY KEY (`id`) USING BTREE
)
COLLATE='utf8mb4_general_ci'
ENGINE=InnoDB
AUTO_INCREMENT=212
;
```

2. Create db.conf file for the script to use

```
[database]
host = ip_or_fqdn_of_db
user = your_user
password = your_pass
database = your_db_name
```

3. Create a file currentDay.conf and place idDnia (day ID) there, taken from the URL of the current voting page:

```
https://www.sejm.gov.pl/Sejm10.nsf/agent.xsp?symbol=listaglos&IdDnia=[TAKE THE NUMBER FROM HERE]
```

4. Run
```
python3 votesToDB.py
```

5. Run

```
python3 generateSite.py
```

6. The result is saved to docs/index.html
