# 🔐 SecureVault – Computer Security Final Project

## 📌 Overview

**SecureVault** is a Flask-based security system developed for the *Computer Security* course. The system simulates real-world secure file operations and user authentication workflows, including:

- ✅ User registration, login, and multi-factor authentication (OTP/TOTP)
- ✅ File encryption/decryption using AES and RSA
- ✅ Digital signature & signature verification
- ✅ Public key sharing via QR code
- ✅ Role-based access control (admin/user)
- ✅ Security activity logging

---

## 🧩 Project Structure

```

/SecureVault/
├── main.py                     # Entry point to launch the Flask app
├── .env                        # Configuration file (DB credentials, email)
├── data/
│   ├── db/
│   │   └── secure\_vault.sql    # SQL script to initialize MySQL database
│   ├── public\_keys/            # Saved public keys (for sharing)
│   ├── encrypted\_files/        # Encrypted file storage
│   └── temp/                   # Temp folder for processing files
├── flaskapi/
│   ├── app.py                  # Flask app setup & route registration
│   ├── routes/
│   │   ├── auth\_routes.py      # Routes for login, MFA, account
│   │   ├── crypto\_routes.py    # File encryption, decryption, signing
│   │   └── utils\_routes.py     # Logs, QR, status checks
│   └── templates/              # HTML pages (Jinja2)
│       └── ...                 # login.html, dashboard.html, etc.
├── modules/
│   ├── auth/                   # MFA, OTP, password hashing
│   ├── crypto/                 # RSA, AES, digital signature functions
│   ├── db/                     # MySQL connection, queries
│   ├── qr/                     # QR code generation & scanning
│   └── utils/                  # Shared utilities: logging, validators
├── static/
│   ├── styles/                 # CSS files
│   ├── scripts/                # JS files
│   └── images/                 # Logo, background, QR images
├── logs/
│   └── security.log            # Security log file for all activities
├── report/
│   ├── final\_report.pdf        # Project report
│   └── screenshots/            # Interface images for documentation
└── README.md                   # This file

````

---

## ⚙️ Setup Instructions

### 1. 🧱 Create and Configure Database

- Create a **MySQL database** named `secure_vault`
- Run the SQL script to initialize schema:

```bash
mysql -u root -p secure_vault < data/db/secure_vault.sql
````

* Update the database credentials in `.env` file:

```
FLASK_SECRET_KEY=02db9b7b9f3a42f6886cf95d91d7e3be0fa96a26d3b8655b8752d2d81e6b1e2 #random secret key
SMTP_USER= <sender mail>
SMTP_PASS= create at https://myaccount.google.com/apppasswords with 2FA account

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_DB = secure_vault
MYSQL_PASSWORD= <your database password>
MYSQL_CURSORCLASS=DictCursor
```

> ⚠️ Don't commit `.env` to public repositories.

---

### 2. ▶️ Run the Flask App

In your terminal:

```bash
python main.py
```

Then open your browser at:

```
http://127.0.0.1:5000/
```

---

## 🧪 Features and How It Works

### 👤 Authentication & MFA

* Users register with email, password, and basic info.
* Passwords are salted and hashed using SHA-256.
* On login, users choose between:

  * OTP via email (expires in 5 minutes)
  * TOTP via Google Authenticator
* Wrong login attempts are limited (lockout for 5 minutes after 5 failures).

### 🔐 RSA Key Management

* Each user can generate 2048-bit RSA key pairs.
* Private key is AES-encrypted with the user's password.
* Public key is saved for sharing and signature verification.

### 🗂 File Encryption & Signature

* Files are encrypted using:

  * AES (for data)
  * RSA (to encrypt AES session key)
* Signed files are created with `.sig` extension.
* Verification checks signatures using public keys in the system.

### 📷 QR Code

* QR codes encode public key + metadata.
* Can be scanned to auto-import public keys.

### 👮‍♂️ Admin Role

* Admin can view all users and activity logs.
* User accounts can be locked/unlocked.
* Activity logs include timestamps, user, action, status.

---

## 🗃 Notes

* All logs are saved in `logs/security.log`
* Encrypted files go into `data/encrypted_files/`
* Public keys are stored in `data/public_keys/`
* QR codes are saved in `static/images/` or user-specific folders





