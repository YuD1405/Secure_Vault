def login_user(email: str, passphrase: str) -> tuple[bool, str]:
    if email == "quangduypham@gmail.com" and passphrase == "123456":
        return True, "Login thành công (test)"
    else:
        return False, "Sai email hoặc mật khẩu (test)"
