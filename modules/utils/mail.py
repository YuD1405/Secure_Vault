import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email(to_email, otp_code):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    
    msg = MIMEMultipart("alternative")
    msg['Subject'] = '[Secure Vault] Your OTP Verification Code'
    msg['From'] = smtp_user
    msg['To'] = to_email
    html_content = f"""
    <html>
      <body>
        <h2>Your Verification Code</h2>
        <p>To verify your account, enter this code in Secure Vault:</p>
        <p style="font-size: 22px;"><strong>{otp_code}</strong></p>
        <p>This code will expire in 5 minutes.</p>
        <br>
        <p style="font-size: 14px; color: gray;">Secure Vault Support Team</p>
      </body>
    </html>
    """
    part = MIMEText(html_content, "html")
    msg.attach(part)
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls() 
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, to_email, msg.as_string())
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
