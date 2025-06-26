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
        return False, "Lỗi: Không thể tạo QR code vì không có khoá nào đang hoạt động."

    public_key_b64 = base64.b64encode(public_info["public_key_pem"].encode()).decode()
    qr_data = {"email": public_info["owner_email"], "creation_date": public_info["creation_date"],
               "public_key_b64": public_key_b64}
    
    json_string = json.dumps(qr_data, separators=(',', ':'))
    img = qrcode.make(json_string)
    img.save(output_path)
    
    return True, f"Đã tạo và lưu QR code thành công tại: {output_path}"

def process_qr_code_and_add_contact(current_user_email: str, qr_image_stream) -> tuple[bool, str]:
    """
    Đọc một file ảnh QR từ stream, giải mã và lưu vào danh bạ.
    """
    try:
        img = Image.open(qr_image_stream)
        decoded_objects = qr_decode(img)
        
        if not decoded_objects:
            return False, "Không tìm thấy mã QR nào trong ảnh."

        qr_data = json.loads(decoded_objects[0].data.decode('utf-8'))
        
        contact_email = qr_data.get('email')
        # ... (phần còn lại của hàm như đã viết trước đó) ...
        
        if contact_email == current_user_email:
            return False, "Bạn không thể thêm chính mình vào danh bạ."

        # ... (xử lý, tạo public_info_to_save) ...
        
        user_dir = get_user_dir(current_user_email)
        add_contact_public_key(user_dir, contact_email, public_info_to_save)
        
        return True, f"Đã thêm thành công {contact_email} vào danh bạ!"

    except Exception as e:
        return False, f"Đã xảy ra lỗi: {e}"
    
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
