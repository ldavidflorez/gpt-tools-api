CREATE EVENT clear_inavalid_jwt ON SCHEDULE EVERY 1 DAY DO 
DELETE FROM 
  invalid_jwt 
WHERE 
  DATE_ADD(
    insertion_date, INTERVAL 240 MINUTE
  ) < CURRENT_DATE();

 SET GLOBAL event_scheduler=ON;