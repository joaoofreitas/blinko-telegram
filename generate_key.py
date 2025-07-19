#!/usr/bin/env python3
"""
Generate a 32-byte encryption key for Blinko Telegram Bot
"""

from cryptography.fernet import Fernet

def generate_encryption_key():
    """Generate a 32-byte encryption key."""
    key = Fernet.generate_key()
    return key.decode()

if __name__ == "__main__":
    print("Generated 32-byte encryption key:")
    print(generate_encryption_key())
    print("\nAdd this to your .env file as ENCRYPTION_KEY=<key>")
