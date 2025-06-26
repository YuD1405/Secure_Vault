import json
import base64
import cv2
from pathlib import Path
 
from pyzbar.pyzbar import decode as qr_decode
from ..crypto.key_extensions import get_user_dir, write_json_file, read_json_file
from ..crypto.key_management import get_active_public_info


QR_DIR = Path("publickey.png")

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
        # 1. Đọc ảnh từ stream sử dụng OpenCV
        # Đọc stream vào một numpy array
        import numpy as np
        image_array = np.frombuffer(qr_image_stream.read(), np.uint8)
        # Decode array thành ảnh mà OpenCV có thể đọc
        img = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

        if img is None:
            return False, "Không thể đọc file ảnh. Vui lòng thử lại với định dạng khác (PNG, JPG)."

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
        # Ở đây chúng ta không có expiry_date từ QR, có thể để trống hoặc tính toán
        # nếu có quy tắc nào đó. Tạm thời để trống.
        public_info_to_save = {
            "owner_email": contact_email,
            "public_key_pem": public_key_pem,
            "creation_date": creation_date,
            "expiry_date": None  # Không có thông tin này từ QR
        }

        # 7. Lấy thư mục của người dùng hiện tại và lưu contact
        user_dir = get_user_dir(current_user_email)
        add_contact_public_key(user_dir, contact_email, public_info_to_save)
        
        return True, f"Đã thêm thành công {contact_email} vào danh bạ của bạn!"

    except json.JSONDecodeError:
        return False, "Nội dung QR code không phải là định dạng JSON hợp lệ."
    except Exception as e:
        return False, f"Đã xảy ra lỗi không xác định: {e}"
    
def add_contact_public_key(user_dir: Path, contact_email: str, public_info: dict):
    """Tiện ích để lưu trữ public_info của một người dùng khác vào danh bạ."""
    contacts_path = user_dir / "contact_public_key.json"
    contacts_data = read_json_file(contacts_path)
    
    contacts_data[contact_email] = public_info
    
    write_json_file(contacts_path, contacts_data)
    print(f"Đã thêm/cập nhật public key của '{contact_email}' vào danh bạ.")


    
def get_all_contacts(current_user_email: str) -> list:
    """
    Lấy toàn bộ danh bạ public key đã lưu của người dùng hiện tại.

    Hàm này đọc file 'contact_public_key.json' trong thư mục của người dùng,
    sau đó chuyển đổi dictionary các contact thành một danh sách (list).

    Args:
        current_user_email (str): Email của người dùng đang đăng nhập.

    Returns:
        Một danh sách các contact, mỗi contact là một dictionary chứa thông tin
        công khai của họ. Trả về một danh sách rỗng nếu không có danh bạ
        hoặc có lỗi xảy ra.
    """
    try:
        # 1. Lấy đường dẫn đến thư mục của người dùng hiện tại
        user_dir = get_user_dir(current_user_email)
        contacts_path = user_dir / "contact_public_key.json"

        # 2. Kiểm tra xem file danh bạ có tồn tại không
        if not contacts_path.exists():
            print(f"Không tìm thấy file danh bạ cho {current_user_email}.")
            return []

        # 3. Đọc và parse file JSON
        # Giả sử bạn có hàm read_json_file, nếu không, dùng code bên dưới
        contacts_data = read_json_file(contacts_path)
        # Hoặc:
        # with open(contacts_path, 'r', encoding='utf-8') as f:
        #     contacts_data = json.load(f)

        # 4. Kiểm tra nếu danh bạ rỗng
        if not contacts_data:
            return []

        # 5. Chuyển đổi từ dictionary sang list
        # contacts_data.values() sẽ lấy tất cả các đối tượng public_info
        # và list() sẽ chuyển chúng thành một danh sách.
        contact_list = list(contacts_data.values())
        
        return contact_list

    except Exception as e:
        # Bắt các lỗi có thể xảy ra (ví dụ: file JSON bị hỏng, lỗi phân quyền,...)
        # và trả về danh sách rỗng để tránh làm sập ứng dụng.
        print(f"Lỗi khi đọc danh bạ của {current_user_email}: {e}")
        return []
