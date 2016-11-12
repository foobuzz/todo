import sqlite3


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
	"""
]


def main():
	conn = sqlite3.connect('data.sqlite')
	for stmt in INIT_DB:
		conn.execute(stmt)


if __name__ == '__main__':
	main()
