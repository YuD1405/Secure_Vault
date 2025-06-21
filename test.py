from modules.utils.mail import send_email
import hashlib
passphrase = "YourPassword123!"
salt = "a1b2c3d4e5f6g7h8"
hashed = hashlib.sha256((passphrase + salt).encode()).hexdigest()
print(hashed)
import pyotp

print(pyotp.random_base32())
