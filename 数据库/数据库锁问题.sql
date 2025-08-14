-- 处理进程死锁问题


-- 查询pg_stat_activity
SELECT
	pg_blocking_pids ( pid ),
	pid,
	now( ) - xact_start,
	wait_event,
	wait_event_type,
	substr( query, 1, 100 ) 
FROM
	pg_stat_activity 
WHERE
	STATE <> 'idle' 
ORDER BY
	3 DESC;
	

SELECT pid, usename, datname, query, state, backend_start, query_start, state_change FROM pg_stat_activity;

-- 查询被锁的pid以及语句：如果state列显示为idle in transaction，则表示被锁了
SELECT pid, state, usename, query, query_start
FROM pg_stat_activity
WHERE pid IN (
    SELECT pid FROM pg_locks l
    JOIN pg_class t ON l.relation = t.oid
    AND t.relkind = 'r'
);

-- 查询所有正在进行的锁定事务和持有的锁定对象：
SELECT pid, relname, transactionid, mode, granted
FROM pg_locks
JOIN pg_stat_user_tables ON pg_locks.relation = pg_stat_user_tables.relid



-- 两种关闭进程的方法
SELECT pg_cancel_backend(4287);
SELECT pg_terminate_backend(4287);