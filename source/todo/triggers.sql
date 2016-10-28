CREATE TRIGGER increment_tallies AFTER INSERT ON Task
BEGIN
	UPDATE Context
	SET own_tasks = own_tasks + 1
	WHERE id = NEW.context;
	UPDATE Context
	SET total_tasks = total_tasks + 1
	WHERE (
		SELECT path
		FROM Context
		WHERE id = NEW.context
	) LIKE path||'%';
END