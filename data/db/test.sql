-- This script is used to set up a test database for secure vault operations
-- and to verify the functionality of the secure vault system.
USE secure_vault;
SHOW TABLES;
SELECT *
FROM users;
SELECT *
FROM otp_codes;

DROP TABLE IF EXISTS users;
SELECT *
FROM users
WHERE email = 'nhdduy22@clc.fitus.edu.vn'