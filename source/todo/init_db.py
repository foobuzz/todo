import sqlite3

from . import utils


INIT_DB = [
	"""
	CREATE TABLE `Task` (
		`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		`title`	TEXT NOT NULL,
		`created`	TEXT NOT NULL DEFAULT (datetime('now')),
		`deadline`	TEXT,
		`start`	TEXT NOT NULL DEFAULT (datetime('now')),
		`priority`	INTEGER NOT NULL DEFAULT 1,
		`done`	TEXT,
		`context`	INTEGER NOT NULL REFERENCES Context(id) ON DELETE CASCADE
	);
	""",
	"""
	CREATE TABLE `Context` (
		`id`	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
		`path`	TEXT NOT NULL UNIQUE,
		`priority`	INTEGER NOT NULL DEFAULT 1,
		`visibility`	TEXT NOT NULL DEFAULT 'normal'
	);
	""",
	"""
	INSERT INTO `Context` (path) VALUES ('')
	""",
	"""
	CREATE INDEX `PathIndex` ON `Context` (`path` ASC);
	""",
	"""
	CREATE INDEX `DoneIndex` ON `Task` (`done`);
	""",
	"""
	CREATE INDEX `DateCreatedIndex` ON `Task` (`created`);
	"""
]


VERSIONS_INDEX = [
	('3.0', 0),
	('3.1', 4)
]


def update_database(path, current_version):
	if current_version is None:
		current_version = '0'
	for i, (version, idx) in enumerate(VERSIONS_INDEX):
		if utils.compare_versions(current_version, version) < 0:
			index = idx
			break
	else:
		index = len(INIT_DB)
	
	updates = INIT_DB[index:]
	if len(updates) > 0:
		conn = sqlite3.connect(path)
		for stmt in updates:
			conn.execute(stmt)
		conn.close()


def main():
	conn = sqlite3.connect('data.sqlite')
	for stmt in INIT_DB:
		conn.execute(stmt)


if __name__ == '__main__':
	main()
