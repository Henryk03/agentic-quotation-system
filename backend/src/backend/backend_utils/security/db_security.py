
import os
from cryptography.fernet import Fernet


__SECRET_KEY = os.environ["SECRET_KEY"]
fernet = Fernet(__SECRET_KEY.encode())


def encrypt(value: str) -> str:
    """"""

    return fernet.encrypt(
        value.encode()
    ).decode()


def decrypt(cipher_value: str) -> str:
    """"""

    return fernet.decrypt(
        cipher_value.encode()
    ).decode()