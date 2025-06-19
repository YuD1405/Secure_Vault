import pyotp
import qrcode
import io
import base64


def get_totp_uri(email, secret):
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="SecureVault")


def generate_qr_base64(uri):
    qr = qrcode.make(uri)
    buffer = io.BytesIO()
    qr.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str
