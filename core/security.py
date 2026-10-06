import hashlib
import secrets


def hash_password(password: str) -> str:
    """Пароль хранится в БД только в виде хэша: «соль$хэш» (scrypt из стандартной библиотеки)."""
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt.encode("utf-8"),
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return f"{salt}${digest.hex()}"
