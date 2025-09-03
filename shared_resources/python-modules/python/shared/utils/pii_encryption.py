import boto3
import json
import os
import base64
from botocore.exceptions import ClientError
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
from Crypto.Random import get_random_bytes


class PIIEncryption:
    def __init__(self):
        self._cached_secret = None
        self._secrets_client = None

    def _get_secrets_client(self):
        if self._secrets_client is None:
            region_name = os.environ["AWS_DEFAULT_REGION"]
            session = boto3.session.Session()
            self._secrets_client = session.client(
                service_name="secretsmanager", region_name=region_name
            )
        return self._secrets_client

    def _get_pii_keys(self):
        if self._cached_secret is not None:
            return self._cached_secret

        secret_name = os.environ.get("PII_ENCRYPTION_SECRET_NAME")
        if not secret_name:
            raise ValueError("PII_ENCRYPTION_SECRET_NAME environment variable not set")

        try:
            client = self._get_secrets_client()
            response = client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response["SecretString"])

            # Decode base64 to get hex string, then convert hex to bytes
            hex_primary = base64.b64decode(secret_data["primary_key"]).decode("utf-8")
            hex_secondary = base64.b64decode(secret_data["secondary_key"]).decode(
                "utf-8"
            )
            hex_salt = base64.b64decode(secret_data["salt"]).decode("utf-8")

            primary_key = bytes.fromhex(hex_primary)
            secondary_key = bytes.fromhex(hex_secondary)
            salt = bytes.fromhex(hex_salt)

            self._cached_secret = {
                "primary_key": primary_key,
                "secondary_key": secondary_key,
                "salt": salt,
                "version": secret_data["version"],
            }

            return self._cached_secret

        except ClientError as e:
            raise e

    def decrypt_pii_payload(self, encrypted_data):
        if not encrypted_data:
            raise ValueError("No encrypted PII data provided")

        keys = self._get_pii_keys()

        try:
            return self._decrypt_with_key(encrypted_data, keys["primary_key"])
        except Exception as primary_error:

            try:
                return self._decrypt_with_key(encrypted_data, keys["secondary_key"])
            except Exception as secondary_error:
                raise ValueError(
                    "PII decryption failed with both keys - data may be corrupted or keys rotated"
                )

    def _decrypt_with_key(self, encrypted_data, key):
        try:
            # Decode base64
            encrypted_bytes = base64.b64decode(encrypted_data)

            iv = encrypted_bytes[:16]
            encrypted_content = encrypted_bytes[16:]

            if len(iv) != 16:
                raise ValueError("Invalid IV length")

            # Create cipher dan decrypt menggunakan AES-CBC
            cipher = AES.new(key, AES.MODE_CBC, iv)
            decrypted_bytes = unpad(cipher.decrypt(encrypted_content), AES.block_size)

            # Convert back to JSON
            decrypted_json = decrypted_bytes.decode("utf-8")
            return json.loads(decrypted_json)

        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_pii_data(self, pii_data, use_secondary=False):
        keys = self._get_pii_keys()
        key = keys["secondary_key"] if use_secondary else keys["primary_key"]

        # Convert to JSON string
        json_string = json.dumps(pii_data, separators=(",", ":"))

        # Generate random IV
        iv = get_random_bytes(16)

        # Create cipher dan encrypt
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(json_string.encode("utf-8"), AES.block_size)
        encrypted_content = cipher.encrypt(padded_data)

        # Combine IV + encrypted content dan encode base64
        encrypted_bytes = iv + encrypted_content
        return base64.b64encode(encrypted_bytes).decode("utf-8")


# Global instance
pii_encryption = PIIEncryption()


# Convenience functions
def decrypt_pii_payload(encrypted_data):
    return pii_encryption.decrypt_pii_payload(encrypted_data)


def encrypt_pii_data(pii_data, use_secondary=False):
    return pii_encryption.encrypt_pii_data(pii_data, use_secondary)
