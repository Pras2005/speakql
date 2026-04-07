from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))


FERNET_KEY = os.getenv("FERNET_KEY")
fernet = Fernet(FERNET_KEY.encode())


def encrypt_password(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_password(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()

