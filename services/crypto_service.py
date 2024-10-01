import os
from cryptography.fernet import Fernet

def load_or_generate_key():
    key_file = 'secret.key'
    if os.path.exists(key_file):
        with open(key_file, 'rb') as f:
            return f.read()
    else:
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)
        return key

def encrypt_file_data(file_data):
    key = load_or_generate_key()
    cipher = Fernet(key)
    return cipher.encrypt(file_data)

def decrypt_file_data(encrypted_data):
    key = load_or_generate_key()
    cipher = Fernet(key)
    return cipher.decrypt(encrypted_data)
