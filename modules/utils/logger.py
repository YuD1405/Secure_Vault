import logging
from datetime import datetime
# Logger cho ROUTE / GIAO DIỆN

logger_user = logging.getLogger("SecureVaultUser")
logger_user.setLevel(logging.INFO)

user_handler = logging.FileHandler('log/security.log')
user_formatter = logging.Formatter('\%(message)s', '%Y-%m-%d %H:%M:%S')
user_handler.setFormatter(user_formatter)

console_user_handler = logging.StreamHandler()
console_user_handler.setFormatter(user_formatter)

logger_user.addHandler(user_handler)
logger_user.addHandler(console_user_handler)

def log_user_action(user_email: str, action: str, status: str, details: str = "", level: str = "info"):
    """
    Ghi log hành động người dùng theo định dạng thống nhất.

    Args:
        user_email (str): Email người dùng thực hiện hành động.
        action (str): Hành động cụ thể (VD: "Đăng ký", "Đăng nhập", "Ký số", ...).
        status (str): Kết quả ("Success", "Fail", "Pending MFA", ...).
        details (str, optional): Thông tin chi tiết (tên file, lỗi, IP, ...).
        level (str, optional): Mức độ log (debug/info/warning/error). Mặc định là "info".
    
    Format chuẩn:
        [2025-07-09 10:15:23] [INFO] [user@example.com] Action=Sign File | Status=Success | Details=file=report.pdf
    """

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    level = level.upper()

    # Xây dựng thông điệp log chi tiết và nhất quán
    msg = f"[{timestamp}] [{level}] [{user_email}] Action={action} | Status={status}"
    if details:
        msg += f" | Details={details}"

    # Gửi về logger phù hợp
    if level == "DEBUG":
        logger_user.debug(msg)
    elif level == "WARNING":
        logger_user.warning(msg)
    elif level == "ERROR":
        logger_user.error(msg)
    else:  # mặc định là INFO
        logger_user.info(msg)

# Logger cho MODULE NỘI BỘ
logger_module = logging.getLogger("SecureVaultModule")
logger_module.setLevel(logging.DEBUG)

module_handler = logging.FileHandler('log/debug_log.log')
module_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
module_handler.setFormatter(module_formatter)

console_module_handler = logging.StreamHandler()
console_module_handler.setFormatter(module_formatter)

logger_module.addHandler(module_handler)
logger_module.addHandler(console_module_handler)

def log_internal_event(module_name: str, message: str, level: str = "info"):
    """
    Logs internal module events for debugging and tracing.

    Args:
        module_name (str): Name of the module (e.g., "crypto").
        message (str): Description of the event.
        level (str): Log level: "info", "debug", "warning", or "error".

    Example log:
        [2025-06-19 14:25:01] [crypto] INFO: Signature generated successfully.
    """

    msg = f"[{module_name}]: {message}"
    if level == "debug":
        logger_module.debug(msg)
    elif level == "warning":
        logger_module.warning(msg)
    elif level == "error":
        logger_module.error(msg)
    else:
        logger_module.info(msg)

def read_security_logs() -> list:
    logs = []
    try:
        with open("log/security.log", "r") as f:
            for line in f:
                try:
                    # VD: [2025-06-19 14:20:00] [INFO]: [user@example.com] Action: Sign file | Status: Success | File: abc.pdf
                    time_part, rest = line.strip().split("] [", 1)
                    timestamp = time_part.strip("[")
                    level, msg = rest.split("]: ", 1)
                    level = level.strip()

                    # Tách email
                    email_start = msg.find('[') + 1
                    email_end = msg.find(']')
                    email = msg[email_start:email_end] if email_start > 0 and email_end > email_start else "Unknown"

                    # Tách status
                    status = "Unknown"
                    if "Status:" in msg:
                        status = msg.split("Status:")[1].split("|")[0].strip()

                    logs.append({
                        "time": timestamp,
                        "level": level,
                        "email": email,
                        "status": status,
                        "message": msg
                    })
                except Exception:
                    continue
    except FileNotFoundError:
        pass
    return logs