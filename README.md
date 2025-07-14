<a id="readme-top"></a>

<div align="center">
  <h1 align="center">Secure Vault – Secure File System & Digital Signing </h1>
  <p align="center">
    A first project for the Computer Security course (CSC15001 - HCMUS). <br> 
  Secure Vault simulates a secure file system with features such as multi-factor authentication, AES-RSA encryption, digital signature, account roles, and recovery.
  </p>
</div>
<p align="center">
  <img src="https://raw.githubusercontent.com/catppuccin/catppuccin/main/assets/palette/macchiato.png" width="400" />
</p>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>

- [1. Project Overview](#1-project-overview)
- [2. Setup and Execution](#2-setup-and-execution)
  - [2.1. Requirements](#21-requirements)
  - [2.2. Database Initialization](#22-database-initialization)
    - [Option 1 – Using MySQL Command Line](#option-1--using-mysql-command-line)
    - [Option 2 – Using GUI](#option-2--using-gui)
  - [2.3. Environment Variables](#23-environment-variables)
  - [2.4. Running the App](#24-running-the-app)
- [3. System Architecture](#3-system-architecture)
  - [3.1. Overall Design](#31-overall-design)
  - [3.2. Project Structure](#32-project-structure)
- [4. Features \& Security Techniques](#4-features--security-techniques)
- [5. Technologies Used](#5-technologies-used)
- [6. Demo \& Testing](#6-demo--testing)
</details>

---

## 1. Project Overview

**Secure Vault** is a secure Flask-based platform allowing users to:
- Register/login with OTP via email or TOTP via Google Authenticator
- Encrypt/decrypt files using AES (GCM) + RSA
- Digitally sign and verify files
- Share public keys via QR code
- Manage role-based access (admin/user), lock accounts
- View full security logs
- Support file format options: combined `.enc` or split `.enc` + `.key`
- Auto-split large files for secure encryption
- Recover accounts using a one-time recovery code

---

## 2. Setup and Execution

### 2.1. Requirements

```bash
pip install -r requirements.txt
```

### 2.2. Database Initialization

You can create the `secure_vault` database using either **command-line** or **GUI tools**:

#### Option 1 – Using MySQL Command Line
```bash
mysql -u root -p
> CREATE DATABASE secure_vault;
> EXIT
```
Then import the schema:
```bash
mysql -u root -p secure_vault < mySQL/secure_vault.sql
```

#### Option 2 – Using GUI

With **phpMyAdmin** (XAMPP, MAMP...):
1. Open your browser and go to `http://localhost/phpmyadmin`
2. Click on **"New"** in the left sidebar
3. Enter `secure_vault` as database name, choose **utf8_general_ci** collation
4. Click **Create**
5. Click on the `secure_vault` database in the left panel
6. Go to **Import** tab at the top
7. Upload the file: `mySQL/secure_vault.sql`
8. Click **Go**

With **MySQL Workbench**:
1. Open MySQL Workbench and connect to your local server
2. Click **File > Open SQL Script**, select `mySQL/secure_vault.sql`
3. Click the **Execute** button
4. The database `secure_vault` will be created automatically with all necessary tables

> Make sure your `.env` file contains matching credentials for MySQL (`root` user or your custom user).


### 2.3. Environment Variables

Create a `.env` file with the following content:

```dotenv
FLASK_SECRET_KEY= <your_secret>
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD= <your_password>
MYSQL_DB=secure_vault
SMTP_USER= <your_gmail>
SMTP_PASS= <google_app_password>
```

### 2.4. Running the App

```bash
python main.py
```

Then open: http://127.0.0.1:5000/

---

## 3. System Architecture

### 3.1. Overall Design

The system is divided into 3 main functional groups:

- **Group 1 – Account & MFA**: register, login, lockout, recovery, role-based access
- **Group 2 – File Encryption/Decryption**: key management, AES + RSA, QR code
- **Group 3 – Signing & Logs**: digital signing, verification, logging, key lookup

### 3.2. Project Structure

```bash
/SECURE_VAULT/
├── data/
│   ├── key_manage/            # Encrypted RSA private/public keys (per user folder)
│   │   └── <user_id_hash>/    # Contains key_<n>.json and contact_public_key.json.
│   ├── qr/                    # QR codes for public keys (grouped by user)
│   │   └── <user_id_hash>/    # Contains qr image
│   └── signature/             # Output folder for digital signatures
├── flaskapi/
│   ├── app.py                 # Flask app initialization
│   ├── extensions.py          # MySQL connector and app extensions
│   └── routes/                # API route handlers (auth, crypto, utils)
├── frontend/
│   ├── static/                # CSS, JS, images
│   └── templates/             # HTML templates (Jinja2)
├── log/
│   ├── security.log           # Log of all security-related actions
│   └── debug_log.log          # Optional debug log
├── modules/
│   ├── auth/                  # Login, MFA, registration, recovery
│   ├── crypto/                # AES, RSA, signing, decryption
│   └── utils/                 # Logging, validators, mail utilities
├── mySQL/
│   ├── secure_vault.sql       # Main DB schema
│   └── test.sql               # Sample test data
├── report/                    # Final report & screenshots
├── .env                       # Environment variables
├── .gitignore
├── ComputerSecurity_PRJ1.pdf  # Assignment description
├── guide_flask.txt            # Flask guide or notes
├── main.py                    # Entry point to run the app
├── README.md
└── requirements.txt
```

---

## 4. Features & Security Techniques

- **Registration**: input validation, SHA-256 hashing with random salt, recovery code generation
- **Login & MFA**:
  - Lock account after 5 wrong attempts (within 2 minutes)
  - OTP (6 digits via email, valid for 5 minutes)
  - TOTP with QR code for Google Authenticator
- **RSA Key Management**:
  - Generate 2048-bit keypair
  - Encrypt private key using AES (derived from passphrase)
  - Set expiration (90 days), allow renewal
- **File Encryption**:
  - Use AES-GCM for file chunks (1MB blocks if >5MB)
  - Encrypt AES session key with recipient’s RSA public key
  - Save format: either combined `.enc` or split `.enc` and `.key`
- **Digital Signing**:
  - Sign file using SHA-256 hash and RSA private key
  - Verify signature using any stored public key
- **QR Code**:
  - Generate/scan QR to import public key
- **Role Management**:
  - Role = `admin` or `user`
  - Admin can lock/unlock users, view system logs
- **Security Logs**:
  - Every event (register, login, encrypt, sign...) logged to `security.log`
- **Account Recovery**:
  - One-time recovery code shown on registration
  - Used to reset password + re-encrypt RSA key

---

## 5. Technologies Used

| Component | Technology / Library        |
| --------- | --------------------------- |
| Backend   | Python Flask                |
| MFA       | pyotp, qrcode, smtplib      |
| Crypto    | pycryptodome (AES-GCM, RSA) |
| Database  | MySQL, Flask-MySQLdb        |
| Frontend  | HTML + CSS + Vanilla JS     |
| Logging   | Custom logger (file-based)  |

---

## 6. Demo & Testing

- Full test cases for:
  - Registration, login, OTP/TOTP verification
  - File encryption/decryption
  - Signing and signature verification
  - Key expiration and renewal
  - Role permissions
  - Account recovery
- Two file storage formats: `.enc` combined or `.enc + .key` split
- Logs all security events with timestamp and status

🔗 [Demo Screenshots & Video](https://drive.google.com/drive/folders/1xRaJ4qGiTHa1X5nbth9Pzn4xKZmUR-6U?usp=sharing)

---
<p align="right">(<a href="#readme-top">Back to top ⬆</a>)</p>




