
-- 查询定时任务
SELECT
  *
FROM
  pg_stat_activity 
WHERE
  query LIKE'%ir_cron%';
	


-- 关闭定时任务
-- id默认为34不动，PG_TERMINATE_BACKEND的值取pid
UPDATE ir_cron
SET active = FALSE
WHERE
  PG_TERMINATE_BACKEND (81559)
  AND id = 34;
	
	
	
-- 死锁
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE datname='xc_materiel' AND pid<>pg_backend_pid();


