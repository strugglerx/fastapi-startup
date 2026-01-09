


from hashlib import md5

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return str(md5(password).hexdigest()).upper()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return str(md5(plain_password).hexdigest()).upper() == hashed_password
