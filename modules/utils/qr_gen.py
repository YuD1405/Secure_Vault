
from ..crypto.gen_private_key import get_active_public_info, base64, json, Path, qr_decode, cv2, get_user_dir, add_contact_public_key
import numpy as np

QR_DIR = Path("QR_output.png")

def generate_public_info_qr(email: str, output_path: str | Path):
    """Tạo mã QR chứa thông tin công khai của khoá đang hoạt động."""
    import qrcode # import tại đây để không bắt buộc phải cài nếu không dùng đến
    print("\n--- [TẠO QR CODE CHO PUBLIC KEY] ---")
    public_info = get_active_public_info(email)
    if not public_info:
        print("Lỗi: Không thể tạo QR code vì không có khoá nào đang hoạt động.")
        return

    public_key_b64 = base64.b64encode(public_info["public_key_pem"].encode()).decode()
    qr_data = {"email": public_info["owner_email"], "creation_date": public_info["creation_date"],
               "public_key_b64": public_key_b64}
    
    json_string = json.dumps(qr_data, separators=(',', ':'))
    img = qrcode.make(json_string)
    img.save(output_path)
    print(f"Đã tạo và lưu QR code thành công tại: {output_path}")


# file: modules/utils/qr_gen.py (hoặc nơi bạn đặt hàm này)

# ... các import ...
import cv2 # Hoặc from PIL import Image nếu bạn dùng Pillow
import numpy as np

# ... các hàm khác ...

def process_qr_code_and_add_contact(current_user_email: str, qr_image_path: str | Path) -> tuple[bool, str]:
    """
    Đọc một file ảnh QR từ đường dẫn, giải mã nội dung, xác thực và lưu vào danh bạ.

    Args:
        current_user_email (str): Email của người dùng đang đăng nhập (để biết lưu vào thư mục nào).
        qr_image_path (str | Path): Đường dẫn đầy đủ đến file ảnh QR (.png, .jpg, ...).

    Returns:
        Một tuple (success: bool, message: str).
    """
    try:
        # --- THAY ĐỔI Ở ĐÂY ---
        # 1. Đọc ảnh trực tiếp từ đường dẫn file sử dụng OpenCV
        img = cv2.imread(str(qr_image_path)) # Dùng str() để đảm bảo tương thích nếu qr_image_path là Path object

        # Nếu bạn dùng Pillow thay vì OpenCV:
        # from PIL import Image
        # img = Image.open(qr_image_path)
        # --- KẾT THÚC THAY ĐỔI ---

        if img is None:
            return False, f"Không thể đọc file ảnh từ đường dẫn: {qr_image_path}"

        # 2. Giải mã QR code từ ảnh
        decoded_objects = qr_decode(img)
        if not decoded_objects:
            return False, "Không tìm thấy mã QR nào trong ảnh."

        # 3. Lấy dữ liệu và phân tích cú pháp JSON
        qr_data_string = decoded_objects[0].data.decode('utf-8')
        qr_data = json.loads(qr_data_string)

        # 4. Xác thực dữ liệu cơ bản
        contact_email = qr_data.get('email')
        creation_date = qr_data.get('creation_date')
        public_key_b64 = qr_data.get('public_key_b64')

        if not all([contact_email, creation_date, public_key_b64]):
            return False, "Dữ liệu từ QR code không đầy đủ hoặc không hợp lệ."
            
        if contact_email == current_user_email:
            return False, "Bạn không thể thêm chính mình vào danh bạ."

        # 5. Giải mã Base64 để lấy public key PEM
        try:
            public_key_pem = base64.b64decode(public_key_b64).decode('utf-8')
        except Exception:
            return False, "Định dạng public key trong QR code không hợp lệ."
            
        # 6. Tạo đối tượng public_info để lưu trữ
        public_info_to_save = {
            "owner_email": contact_email,
            "public_key_pem": public_key_pem,
            "creation_date": creation_date,
            "expiry_date": None
        }

        # 7. Lấy thư mục của người dùng hiện tại và lưu contact
        user_dir = get_user_dir(current_user_email)
        add_contact_public_key(user_dir, contact_email, public_info_to_save)
        
        return True, f"Đã thêm thành công {contact_email} vào danh bạ của bạn!"

    except FileNotFoundError:
        return False, f"Không tìm thấy file tại đường dẫn: {qr_image_path}"
    except json.JSONDecodeError:
        return False, "Nội dung QR code không phải là định dạng JSON hợp lệ."
    except Exception as e:
        return False, f"Đã xảy ra lỗi không xác định: {e}"
    
process_qr_code_and_add_contact("hoangdat220404@gmail.com",QR_DIR)