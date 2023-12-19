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
	""",
	"""
	ALTER TABLE Task ADD COLUMN `content` TEXT
	""",
	"""
	ALTER TABLE Task ADD COLUMN `editing` INTEGER NOT NULL DEFAULT 0
	""",
	"""
	CREATE TABLE `TaskDependency` (
		`task_id`	INTEGER NOT NULL REFERENCES Task(id) ON DELETE CASCADE,
		`dependency_id`	INTEGER NOT NULL REFERENCES Task(id) ON DELETE CASCADE
	);
	""",
	"""
	CREATE INDEX `TaskDependerIndex` ON `TaskDependency` (`task_id`);
	""",
	"""
	CREATE INDEX `TaskDependeeIndex` ON `TaskDependency` (`dependency_id`);
	""",
	"""
	ALTER TABLE Task ADD COLUMN `ping` INTEGER NOT NULL DEFAULT 0
	""",
	"""
	ALTER TABLE Task ADD COLUMN `period` INTEGER
	""",
	"""
	CREATE TABLE `TaskDoneHistory` (
		`task_id`	INTEGER NOT NULL REFERENCES Task(id) ON DELETE CASCADE,
		`done_datetime`	TEXT NOT NULL
	);
	""",
	"""
	CREATE INDEX `TaskDoneHistoryIndex` ON `TaskDoneHistory` (`task_id`);
	""",
	"""
	ALTER TABLE Task ADD COLUMN `front` INTEGER
	"""
]


VERSIONS_INDEX = [
	('3.0', 0),
	('3.1', 4),
	('3.2', 6),
	('4.0.0', 8),
	('5.0.0', 12),
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
		conn = sqlite3.connect(path, isolation_level=None)
		for stmt in updates:
			conn.execute(stmt)
		conn.commit()
		conn.close()


def main():
	conn = sqlite3.connect('data.sqlite')
	for stmt in INIT_DB:
		conn.execute(stmt)


if __name__ == '__main__':
	main()
