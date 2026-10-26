-- Industrial Energy Intelligence Platform (IEIP)
-- Retention Prune Script: Removes furnace_readings older than 7 days

USE furnace_db;

-- Delete time-series points older than 7 days
DELETE FROM furnace_readings 
WHERE ts < NOW() - INTERVAL 7 DAY;
