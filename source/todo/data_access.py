import sqlite3, json, os
import os.path as op
from datetime import datetime

from . import utils


DATA_DIR_NAME = '.toduh'
DATAFILE_NAME = 'data.json'
DATABASE_NAME = 'data.sqlite'
DATA_CTX_NAME = 'contexts'

# If a .toduh exists in the current working directory, it's used by the
# program. Otherwise the one in the home is used.
if op.exists(DATA_DIR_NAME) and op.isdir(DATA_DIR_NAME):
	DATA_DIR = DATA_DIR_NAME
else:
	DATA_DIR = op.expanduser(op.join('~', '.toduh'))

DB_PATH = op.join(DATA_DIR, DATABASE_NAME)


def setup_data_access():
	if not op.exists(DATA_DIR):
		os.makedirs(DATA_DIR)
	# Three possibilities:
	#  - We find the sqlite database (v3+). Nothing to do
	#  - We find the JSON file (v2.2-). We need to set the database up and
	#    transfer the data from JSON to the database
	#  - We find nothing. We need to set the database up.
	json_path = op.join(DATA_DIR, DATAFILE_NAME)
	if op.exists(DB_PATH):
		pass
	elif op.exists(json_path):
		connection = setup_database(DB_PATH)
		with open(json_path) as datafile:
			data = json.load(datafile)
		transfer_data(connection, data)
	else:
		setup_database(DB_PATH).close()
	return DB_PATH


def setup_database(db_path):
	from .init_db import INIT_DB
	conn = sqlite3.connect(db_path)
	c = conn.cursor()
	for stmt in INIT_DB:
		c.execute(stmt)
	conn.commit()
	return conn


def transfer_data(connection, data):
	daccess = DataAccess(connection)
	for ctx, props in data['contexts'].items():
		ctx = dbfy_context(ctx)
		options = []
		if 'p' in props:
			options.append(('priority', props['p']))
		if 'v' in props and props['v'] == 'hidden':
			options.append(('visibility', 'hidden'))
		daccess.get_or_create_context(ctx, options)
	for task in data['tasks']:
		title = task['content']
		if 'context' in task:
			ctx = dbfy_context(task['context'])
			daccess.get_or_create_context(ctx)
		else:
			ctx = ''

		options = []
		if 'created' in task:
			created = iso2sqlite(task['created'])
		else:
			created = datetime.min.strftime(utils.SQLITE_DT_FORMAT)
		options.append(('created', created))
		for prop in ['start', 'deadline']:
			if prop in task:
				options.append((prop, iso2sqlite(task[prop])))
		if 'done' in task and task['done']:
			options.append(('done', '1'))
		if 'priority' in task:
			options.append(('priority', task['priority']))
		daccess.add_task(title, ctx, options)
	daccess.exit()


def dbfy_context(ctx):
	if ctx == '' or ctx.startswith('.'):
		return ctx
	else:
		return '.'+ctx


def userify_context(ctx):
	if ctx == '':
		return ''
	else:
		return ctx[1:]


def iso2sqlite(iso_date):
	dt = datetime.strptime(iso_date, utils.ISO_DATE)
	return dt.strftime(utils.SQLITE_DT_FORMAT)


def get_insert_components(options):
	col_names = ','.join(opt[0] for opt in options)
	placeholders = ','.join('?' for i in range(len(options)))
	if len(col_names) > 0:
		col_names = ',' + col_names
	if len(placeholders) > 0:
		placeholders = ',' + placeholders
	values = tuple(opt[1] for opt in options)
	return col_names, placeholders, values


def get_update_components(options):
	placeholders = ','.join(
		'{}=?'.format(opt[0])
		for opt in options
	)
	values = tuple(opt[1] for opt in options)
	return placeholders, values


def rename_context(path, name):
	return '.'.join(path.split('.')[:-1]+[name])


class DataAccess():

	def __init__(self, connection):
		self.connection = connection
		c = self.connection.cursor()
		c.execute('PRAGMA case_sensitive_like = ON;')
		c.execute('PRAGMA foreign_keys = ON;')
		self.connection.row_factory = sqlite3.Row
		self.added_context = False

	def add_task(self, title, context='', options=[]):
		cid = self.get_or_create_context(context)
		query_tmp = """
			INSERT INTO Task (title, context {})
			VALUES (?, ? {})
		"""
		col_names, placeholders, values = get_insert_components(options)
		values = (title, cid) + values
		query = query_tmp.format(col_names, placeholders)

		c = self.connection.cursor()
		c.execute(query, values)
		return c.lastrowid

	def update_task(self, tid, context=None, options=[]):
		if context is not None:
			cid = self.get_or_create_context(context)
			options = options.copy()
			options.append(('context', cid))
		query_tmp = """
			UPDATE Task SET {}
			WHERE id = ?
		"""
		placeholders, values = get_update_components(options)
		values += (tid,)
		query = query_tmp.format(placeholders)

		c = self.connection.cursor()
		c.execute(query, values)
		return c.rowcount

	def get_task(self, tid, columns='*'):
		query = """
			SELECT {}
			FROM Task
			WHERE id = ?
		""".format(columns)

		c = self.connection.cursor()
		c.execute(query, (tid,))
		row = c.fetchone()
		if row is None:
			return None
		return row

	def do_many(self, function, tids):
		missing = []
		for tid in tids:
			updated = getattr(self, function)(tid)
			if updated == 0:
				missing.append(tid)
		return missing

	def set_done_many(self, tids):
		return self.do_many('set_done', tids)

	def remove_many(self, tids):
		return self.do_many('remove', tids)

	def set_done(self, tid):
		c = self.connection.cursor()
		c.execute("""
			UPDATE Task SET done = datetime('now')
			WHERE id = ?
			AND done IS NULL
		""", (tid,))
		return c.rowcount

	def remove(self, tid):
		c = self.connection.cursor()
		c.execute("""
			DELETE FROM Task
			WHERE id = ?
		""", (tid,))
		return c.rowcount

	def get_or_create_context(self, path, options=[]):
		ctxs = path.split('.')[1:]
		path_so_far = ''
		c = self.connection.cursor()
		for ctx in ctxs:
			path_so_far += '.'+ctx
			try:
				c.execute("""
					INSERT INTO Context (path)
					VALUES (?)
				""", (path_so_far,))
			except sqlite3.IntegrityError: # Already exists
				continue
			else:
				self.added_context = True

		query_tmp = """
			INSERT INTO Context (path {})
			VALUES (? {})
		"""
		col_names, placeholders, values = get_insert_components(options)
		query = query_tmp.format(col_names, placeholders)

		try:
			c.execute(query, (path,) + values)
		except sqlite3.IntegrityError as e:
			c2 = self.connection.cursor()
			c2.execute("""
				SELECT id FROM Context
				WHERE path = ?
			""", (path,))
			row = c2.fetchone()
			return row[0]
		else:
			self.added_context = True
			return c.lastrowid

	def context_exists(self, path):
		c = self.connection.cursor()
		c.execute("""
			SELECT 1 FROM Context
			WHERE path = ?
		""", (path,))
		row = c.fetchone()
		return row is not None
		
	def set_context(self, path, options=[]):
		cid = self.get_or_create_context(path)
		query_tmp = """
			UPDATE Context SET {}
			WHERE id = ?
		"""
		placeholders, values = get_update_components(options)
		query = query_tmp.format(placeholders)

		c = self.connection.cursor()
		c.execute(query, values + (cid,))
		return c.rowcount

	def move(self, ctx1, ctx2):
		cid = self.get_or_create_context(ctx2)
		c = self.connection.cursor()
		c.execute("""
			UPDATE Task
			SET context = ?
			WHERE context = (
				SELECT id FROM Context
				WHERE path = ?
			)
		""", (cid, ctx1))

	def remove_context(self, path):
		c = self.connection.cursor()
		c.execute("""
			DELETE FROM Context
			WHERE path LIKE ?
		""", ('{}%'.format(path),))
		return c.rowcount

	def rename_context(self, path, name):
		"""Rename context with given path with name. Returns None if new name
		already exists, number of row affected otherwise.
		"""
		renamed = rename_context(path, name)
		# Lock the db at the first select to avoid race conditions
		self.connection.isolation_level = 'IMMEDIATE'
		# If the context (after renaming) already exists, abort
		c = self.connection.cursor()
		c.execute("""
			SELECT 1 FROM Context WHERE path = ?
		""", (renamed,))
		if c.fetchone() is not None:
			return None
		# We need to rename all the subcontexts as well. Can't do it in one
		# UPDATE query because sqlite's REPLACE would replace all occurrences
		# and we risk renaming other things (contexts whose same structure
		# repeats at a sub-level)
		c = self.connection.cursor()
		c.execute("""
			SELECT id, path FROM Context WHERE path LIKE ?
		""", ('{}%'.format(path),))
		new = ((renamed + row['path'][len(path):], row['id']) for row in c)
		c2 = self.connection.cursor()
		c2.executemany("""
			UPDATE Context
			SET path = ?
			WHERE ID = ?
		""", new)
		return c2.rowcount

	def todo(self, path=''):
		c = self.connection.cursor()
		c.execute("""
			SELECT t.*, c.path as ctx_path
			FROM Task t JOIN Context c
			ON t.context = c.id
			WHERE c.path = ?
			  AND t.done IS NULL
			  AND (datetime('now')) >= datetime(t.start)
			ORDER BY
			  priority DESC,
			  COALESCE(
			      julianday(deadline),
			      julianday('9999-12-31 23:59:59')
			    ) - julianday('now') ASC,
			  created ASC
		""", (path,))
		return c.fetchall()

	def get_subcontexts(self, path=''):
		c = self.connection.cursor()
		c.execute("""
			SELECT c.*, COUNT(own.id) as own_tasks, (
				SELECT COUNT(t.id)
				FROM Context c1
				LEFT JOIN Task t
				  ON t.context = c1.id
				 AND t.start <= (datetime('now'))
				 AND t.done IS NULL
				WHERE c1.path LIKE c.path||'%' 
			) as total_tasks
			FROM Context c
			LEFT JOIN Task own
			  ON own.context = c.id
			 AND own.start <= (datetime('now'))
			 AND own.done IS NULL
			WHERE path LIKE ?
			  AND path NOT LIKE ?
			  AND total_tasks > 0
			  AND visibility = 'normal'
			GROUP BY c.id
			ORDER BY
			  priority DESC,
			  total_tasks DESC
		""", (
			'{}.%'.format(path),
			'{}.%.%'.format(path)
			)
		)
		return c.fetchall()

	def get_descendants(self, path=''):
		c = self.connection.cursor()
		c.execute("""
			SELECT c.*, COUNT(own.id) as own_tasks, (
				SELECT COUNT(t.id)
				FROM Context c1
				LEFT JOIN Task t
				  ON t.context = c1.id
				 AND t.start <= (datetime('now'))
				 AND t.done IS NULL
				WHERE c1.path LIKE c.path||'%' 
			) as total_tasks
			FROM Context c
			LEFT JOIN Task own
			  ON own.context = c.id
			 AND own.start <= (datetime('now'))
			 AND own.done IS NULL
			WHERE path LIKE ?
			GROUP BY c.id
			ORDER BY
			  c.path
		""", ('{}%'.format(path),))
		return c

	def history(self):
		c = self.connection.cursor()
		c.execute("""
			SELECT t.*, c.path as ctx_path
			FROM Task t JOIN Context c
			ON t.context = c.id
			ORDER BY t.created
		""")
		return c

	def get_greatest_id(self):
		c = self.connection.cursor()
		c.execute("""
			SELECT MAX(id)
			FROM Task
		""")
		row = c.fetchone()
		if row is None:
			return None
		else:
			return row[0]

	def purge(self, before):
		c = self.connection.cursor()
		query = """
			DELETE FROM Task
			WHERE done IS NOT NULL
		"""
		if before is not None:
			query += """
				AND created < ?
			"""
			values = (before,)
		else:
			values = ()
		c.execute(query, values)
		return c.rowcount

	def exit(self, save=True):
		if save:
			self.connection.commit()
			if self.added_context:
				c = self.connection.cursor()
				c.execute("""
					SELECT DISTINCT path FROM Context
					ORDER BY path
				""")
				data_ctx = op.join(DATA_DIR, DATA_CTX_NAME)
				with open(data_ctx, 'w') as ctx_file:
					for row in c:
						ctx = userify_context(row[0])
						ctx_file.write(ctx + '\n')
		self.connection.close()
