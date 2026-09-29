from cryptography.fernet import Fernet
from core.config import settings

# Initialize Fernet with the key from settings
fernet = Fernet(settings.FERNET_KEY.encode())

def encrypt_password(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()

def decrypt_password(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
