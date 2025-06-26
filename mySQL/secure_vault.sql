-- Create a secure vault connection at port 3306 before running this script.
-- Remember to modify the database password in flaskapi/app.py
-- to match the root password of the secure vault database.
CREATE DATABASE secure_vault CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE secure_vault;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    fullname VARCHAR(255),
    dob DATE,
    phone VARCHAR(20),
    address TEXT,
    salt VARCHAR(64),
    hashed_passphrase VARCHAR(128),
    role ENUM('admin', 'user') DEFAULT 'user',
    mfa_secret VARCHAR(64),
    recovery_code VARCHAR(64),
    is_locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    failed_attempts INT DEFAULT 0,
    last_failed_login DATETIME
);

INSERT INTO users (
    email, fullname, dob, phone, address,
    salt, hashed_passphrase, recovery_code, role
)
VALUES (
    'admin@fitus.edu.vn',
    'Administrator',
    '1990-01-01',
    '0123456789',
    'System HQ',
    'a1b2c3d4e5f6g7h8',
    'eb83a5fbfe4f6b9857f7e08013852afced14b172b05f2407b50bc6fb6d42d2f2',
    'ADMIN_DEPTRAI_123@@',
    'admin'
);

CREATE TABLE otp_codes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  email VARCHAR(255),
  otp_code VARCHAR(6),
  created_at DATETIME,
  expires_at DATETIME
);
