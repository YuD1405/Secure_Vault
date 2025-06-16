# 🔐 Computer Security Project – SecureVault

## 📌 Mô tả
Đây là đồ án môn **An ninh máy tính**, mô phỏng một hệ thống bảo mật cơ bản bao gồm:
- Đăng ký & đăng nhập người dùng có xác thực OTP/TOTP (MFA)
- Tạo, quản lý và sử dụng khóa RSA/AES để mã hóa – giải mã tập tin
- Chữ ký số, xác minh chữ ký, quét/tạo QR chứa public key
- Quản lý tài khoản người dùng, phân quyền admin
- Ghi log bảo mật toàn bộ hoạt động hệ thống

---

## 🏗 Cấu trúc thư mục

```bash
/SecureVault/
├── main.py                  # Chạy chương trình chính
├── frontend/                # Giao diện người dùng
│   ├── index.html
│   ├── styles.css
│   └── scripts.js
├── gui/                     # API liên kết modules và frontend      
│   └── app.py            
├── modules/                 # Các chức năng được chia theo module
│   ├── auth.py              # Xử lý đăng ký, đăng nhập, MFA
│   ├── key_manager.py       # Quản lý RSA, AES
│   ├── file_crypto.py       # Mã hóa / Giải mã tập tin
│   ├── signer.py            # Ký số / xác minh
│   └── utils.py             # Tiện ích dùng chung (log, QR, validate)
├── data/                    # Dữ liệu người dùng, khóa, file test
│   ├── users.json
│   ├── public_keys/
│   └── encrypted_files/
├── logs/
│   └── security.log         # Log hoạt động
├── report/                  # Báo cáo PDF, hình ảnh minh họa
├── README.md                # Hướng dẫn tổng quát
