from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

KEY_SIZE = 16  # 128-bit AES


def generate_key():
    """Generate a random AES-128 encryption key."""
    return get_random_bytes(KEY_SIZE)


def encrypt_bytes(data: bytes, key: bytes) -> bytes:
    """
    Encrypt data using AES-CBC with PKCS7 padding.
    Returns IV + ciphertext.
    """
    if not isinstance(data, bytes):
        raise TypeError("Data must be bytes")
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes")
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ciphertext


def decrypt_bytes(encrypted_data: bytes, key: bytes) -> bytes:
    """
    Decrypt AES-CBC encrypted data.
    Expects IV prepended to ciphertext.
    """
    if len(encrypted_data) < AES.block_size:
        raise ValueError("Encrypted data is too short — missing IV")
    if len(key) != KEY_SIZE:
        raise ValueError(f"Key must be {KEY_SIZE} bytes")
    iv = encrypted_data[:AES.block_size]
    ciphertext = encrypted_data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ciphertext), AES.block_size)
