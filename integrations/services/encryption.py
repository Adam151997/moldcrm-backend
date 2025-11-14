"""
Encryption utilities for securing API keys and sensitive data
"""
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import hashlib


def get_encryption_key():
    """
    Get or generate encryption key from Django settings
    Uses SECRET_KEY as base for generating a Fernet-compatible key
    """
    # Use Django's SECRET_KEY to derive a Fernet key
    key_material = settings.SECRET_KEY.encode()
    # Create a 32-byte key using SHA256
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return key


def encrypt_api_key(api_key: str) -> str:
    """
    Encrypt an API key for storage

    Args:
        api_key: The plain text API key

    Returns:
        Encrypted API key as a string
    """
    if not api_key:
        return ""

    key = get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(api_key.encode())
    return encrypted.decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """
    Decrypt an API key for use

    Args:
        encrypted_key: The encrypted API key

    Returns:
        Decrypted API key as a string
    """
    if not encrypted_key:
        return ""

    try:
        key = get_encryption_key()
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except Exception as e:
        # Log the error in production
        print(f"Decryption error: {e}")
        return ""


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask an API key for display purposes

    Args:
        api_key: The API key to mask
        visible_chars: Number of characters to show at start and end

    Returns:
        Masked API key (e.g., "sk_t...j7k2")
    """
    if not api_key:
        return ""

    if len(api_key) <= visible_chars * 2:
        return "*" * len(api_key)

    return f"{api_key[:visible_chars]}...{api_key[-visible_chars:]}"
