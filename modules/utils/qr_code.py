import json
import base64
import cv2
from pathlib import Path
 
from pyzbar.pyzbar import decode as qr_decode
from modules.crypto.key_extensions import get_user_dir, write_json_file, read_json_file
from modules.crypto.key_management import get_active_public_info

QR_DIR = Path("publickey.png")

def generate_public_info_qr(email: str, output_path: str | Path):
    """Tạo mã QR chứa thông tin công khai của khoá đang hoạt động."""
    import qrcode # import tại đây để không bắt buộc phải cài nếu không dùng đến
    print("\n--- [TẠO QR CODE CHO PUBLIC KEY] ---")
    public_info = get_active_public_info(email)
    if not public_info:
        return False, "Error: Unable to generate QR code because no active key is available."


    public_key_b64 = base64.b64encode(public_info["public_key_pem"].encode()).decode()
    qr_data = {"email": public_info["owner_email"], "creation_date": public_info["creation_date"], "expired_date": public_info["expiry_date"],
               "public_key_b64": public_key_b64}
    
    json_string = json.dumps(qr_data, separators=(',', ':'))
    img = qrcode.make(json_string)
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    img.save(output_path)
    
    return True, f"QR code generated and saved successfully at: {output_path}"

def process_qr_code_and_add_contact(current_user_email: str, qr_image_stream) -> tuple[bool, str]:
    """
    Đọc một file ảnh QR, giải mã nội dung, xác thực và lưu vào danh bạ.

    Args:
        current_user_email (str): Email của người dùng đang đăng nhập (để biết lưu vào thư mục nào).
        qr_image_stream: Một đối tượng file-like stream của ảnh được upload.

    Returns:
        Một tuple (success: bool, message: str).
    """
    try:
        import numpy as np

        qr_image_stream.seek(0)
        qr_image_bytes = qr_image_stream.read()

        image_array = np.frombuffer(qr_image_bytes, np.uint8)
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if img is None:
            return False, "Unable to read the image file. Please try again with a different format (PNG, JPG)."
        
        decoded_objects = qr_decode(img)
        if not decoded_objects:
            return False, "No QR code found in the image."

        # 3. Lấy dữ liệu và phân tích cú pháp JSON
        qr_image_base64 = "data:image/png;base64," + base64.b64encode(qr_image_bytes).decode('utf-8')
        qr_data_string = decoded_objects[0].data.decode('utf-8')
        qr_data = json.loads(qr_data_string)

        # 4. Xác thực dữ liệu cơ bản
        contact_email = qr_data.get('email')
        creation_date = qr_data.get('creation_date')
        expiry_date = qr_data.get('expired_date')
        public_key_b64 = qr_data.get('public_key_b64')

        if not all([contact_email, creation_date, public_key_b64]):
            return False, "QR code data is incomplete or invalid."
            
        if contact_email == current_user_email:
            return False, "You cannot add yourself to your own contact list."

        # 5. Giải mã Base64 để lấy public key PEM
        try:
            public_key_pem = base64.b64decode(public_key_b64).decode('utf-8')
        except Exception:
            return False, "Invalid public key format in QR code."
            
        # 6. Tạo đối tượng public_info để lưu trữ
        # Ở đây chúng ta không có expiry_date từ QR, có thể để trống hoặc tính toán
        # nếu có quy tắc nào đó. Tạm thời để trống.
        public_info_to_save = {
            "owner_email": contact_email,
            "public_key_pem": public_key_pem,
            "creation_date": creation_date,
            "expiry_date": expiry_date,
            "qr_image": qr_image_base64 
        }

        # 7. Lấy thư mục của người dùng hiện tại và lưu contact
        user_dir = get_user_dir(current_user_email)
        add_contact_public_key(user_dir, contact_email, public_info_to_save)
        
        return True, f"Successfully added {contact_email} to your contact list!"

    except json.JSONDecodeError:
        return False, "QR code content is not a valid JSON format."
    except Exception as e:
        return False, f"An error occurred: {e}"
    
def add_contact_public_key(user_dir: Path, contact_email: str, public_info: dict):
    """Tiện ích để lưu trữ public_info của một người dùng khác vào danh bạ."""
    contacts_path = user_dir / "contact_public_key.json"
    contacts_data = read_json_file(contacts_path)
    
    contacts_data[contact_email] = public_info
    
    write_json_file(contacts_path, contacts_data)
    print(f"Đã thêm/cập nhật public key của '{contact_email}' vào danh bạ.")

def get_all_contacts(current_user_email: str) -> list:
    try:
        user_dir = get_user_dir(current_user_email)

        contacts_path = user_dir / "contact_public_key.json"
        if not contacts_path.exists():
            print(f"Không tìm thấy file danh bạ cho {current_user_email}.")
            return []

        contacts_data = read_json_file(contacts_path)
        
        if not contacts_data:

            return []

        contact_list = list(contacts_data.values())
        return contact_list

    except Exception as e:
        print(f"Lỗi khi đọc danh bạ của {current_user_email}: {e}")
        return []