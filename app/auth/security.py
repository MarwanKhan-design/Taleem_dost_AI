import hashlib
import hmac
import secrets

ITERATIONS = 310_000
SALT_BYTES = 16

def hash_password(password: str):
    """Return a random salt and PBKDF2-HMAC-SHA256 password hash."""
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return salt.hex(), digest.hex()

def verify_password(password: str, salt_hex: str, expected_hash_hex: str) -> bool:
    try:
        salt = bytes.fromhex(salt_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS).hex()
        return hmac.compare_digest(actual, expected_hash_hex)
    except (ValueError, TypeError):
        return False

def validate_password(password: str):
    if len(password) < 10:
        return "Use at least 10 characters."
    if not any(ch.isalpha() for ch in password):
        return "Include at least one letter."
    if not any(ch.isdigit() for ch in password):
        return "Include at least one number."
    return None
