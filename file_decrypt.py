from cryptography.fernet import Fernet
import json

ENCRYPTION_KEY = b'JZfpG9N5K4PQoQMtImxPv80DS-D-WPXr9DN0eF7zhR4='
def encrypt_data(data):
    fernet = Fernet(ENCRYPTION_KEY)
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data


def decrypt_data(encrypted_data):
    fernet = Fernet(ENCRYPTION_KEY)
    decrypted_data = fernet.decrypt(encrypted_data).decode()
    return decrypted_data


def load_remaining_actions(file):
    with open(file, 'rb') as file:
        encrypted_data = file.read()
        decrypted_data = decrypt_data(encrypted_data)
        data = json.loads(decrypted_data)
        print(data)

if __name__ == '__main__':
    file = r"C:\Users\71958\Downloads\temp_action_and_num.json"
    load_remaining_actions(file)