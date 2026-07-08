import os
from cryptography.fernet import Fernet

# Use a fixed key for simplicity, or generate one if not provided
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", b"c7b1tE-0O9Q1j_D9uH3Qf0A2kK5M-Y4nN6H8h7R1f0s=")

# Ensure key is valid bytes
try:
    f = Fernet(ENCRYPTION_KEY)
except ValueError:
    key = Fernet.generate_key()
    f = Fernet(key)
    print(f"Warning: Invalid ENCRYPTION_KEY. Generated temporary key: {key.decode()}")

def encrypt_key(plain_text: str) -> str:
    return f.encrypt(plain_text.encode()).decode()

def decrypt_key(encrypted_text: str) -> str:
    return f.decrypt(encrypted_text.encode()).decode()
