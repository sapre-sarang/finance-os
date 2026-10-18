from cryptography.fernet import Fernet, InvalidToken


class FieldCipher:
    """Encrypts individual sensitive column values (authenticated, AES-128-CBC + HMAC)."""

    def __init__(self, key: str) -> None:
        try:
            self._fernet = Fernet(key.encode())
        except ValueError as error:
            raise ValueError("ENCRYPTION_KEY must be 32 bytes of URL-safe base64") from error

    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode())

    def decrypt(self, token: bytes) -> str:
        try:
            return self._fernet.decrypt(token).decode()
        except InvalidToken:
            raise ValueError("encrypted value cannot be decrypted with this key") from None
