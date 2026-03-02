
import os
from cryptography.fernet import Fernet


__SECRET_KEY = os.environ["SECRET_KEY"]
fernet = Fernet(__SECRET_KEY.encode())


def encrypt(
        value: str
    ) -> str:
    """
    Encrypt a string using Fernet symmetric encryption.

    Parameters
    ----------
    value : str
        The plaintext string to encrypt.

    Returns
    -------
    str
        The encrypted string encoded in base64.
    """

    return fernet.encrypt(
        value.encode()
    ).decode()


def decrypt(
        cipher_value: str
    ) -> str:
    """
    Decrypt a string previously encrypted with Fernet.

    Parameters
    ----------
    cipher_value : str
        The encrypted string to decrypt.

    Returns
    -------
    str
        The original plaintext string.
    """

    return fernet.decrypt(
        cipher_value.encode()
    ).decode()