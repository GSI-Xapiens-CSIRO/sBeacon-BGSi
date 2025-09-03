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
            print("DEBUG - Using cached secret")
            return self._cached_secret

        secret_name = os.environ.get("PII_ENCRYPTION_SECRET_NAME")
        if not secret_name:
            raise ValueError("PII_ENCRYPTION_SECRET_NAME environment variable not set")

        print(f"DEBUG - Fetching secret: {secret_name}")

        try:
            client = self._get_secrets_client()
            response = client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response["SecretString"])

            print(f"DEBUG - Secret retrieved successfully")
            print(f"DEBUG - Secret keys available: {list(secret_data.keys())}")
            print(
                f"DEBUG - Primary key raw (first 20 chars): {secret_data['primary_key'][:20]}..."
            )
            print(f"DEBUG - Primary key length: {len(secret_data['primary_key'])}")
            print(f"DEBUG - Secondary key length: {len(secret_data['secondary_key'])}")
            print(f"DEBUG - Salt length: {len(secret_data['salt'])}")
            print(f"DEBUG - Version: {secret_data.get('version', 'N/A')}")

            try:
                # Step 1: Decode base64 to get hex string
                print("DEBUG - Step 1: Decoding base64...")
                hex_primary = base64.b64decode(secret_data["primary_key"]).decode(
                    "utf-8"
                )
                hex_secondary = base64.b64decode(secret_data["secondary_key"]).decode(
                    "utf-8"
                )
                hex_salt = base64.b64decode(secret_data["salt"]).decode("utf-8")

                print(f"DEBUG - Hex primary (first 20 chars): {hex_primary[:20]}...")
                print(f"DEBUG - Hex primary length: {len(hex_primary)}")
                print(f"DEBUG - Hex secondary length: {len(hex_secondary)}")
                print(f"DEBUG - Hex salt length: {len(hex_salt)}")

                # Step 2: Convert hex string to bytes
                print("DEBUG - Step 2: Converting hex to bytes...")
                primary_key = bytes.fromhex(hex_primary)
                secondary_key = bytes.fromhex(hex_secondary)
                salt = bytes.fromhex(hex_salt)

                print(f"DEBUG - Final primary key length: {len(primary_key)} bytes")
                print(f"DEBUG - Final secondary key length: {len(secondary_key)} bytes")
                print(f"DEBUG - Final salt length: {len(salt)} bytes")

                # Validate key lengths
                if len(primary_key) != 32:
                    raise ValueError(
                        f"Primary key must be 32 bytes, got {len(primary_key)} bytes"
                    )
                if len(secondary_key) != 32:
                    raise ValueError(
                        f"Secondary key must be 32 bytes, got {len(secondary_key)} bytes"
                    )
                if len(salt) != 16:
                    raise ValueError(f"Salt must be 16 bytes, got {len(salt)} bytes")

                print("DEBUG - Key validation passed ✓")

                self._cached_secret = {
                    "primary_key": primary_key,
                    "secondary_key": secondary_key,
                    "salt": salt,
                    "version": secret_data["version"],
                }

                print("DEBUG - Secret cached successfully ✓")
                return self._cached_secret

            except Exception as decode_error:
                print(f"DEBUG - Decoding error: {str(decode_error)}")
                print(f"DEBUG - Error type: {type(decode_error).__name__}")
                raise ValueError(f"Failed to decode secret data: {str(decode_error)}")

        except ClientError as e:
            print(
                f"DEBUG - AWS ClientError: {e.response['Error']['Code']} - {e.response['Error']['Message']}"
            )
            raise e
        except json.JSONDecodeError as e:
            print(f"DEBUG - JSON decode error: {str(e)}")
            raise ValueError(f"Invalid JSON in secret: {str(e)}")
        except Exception as e:
            print(f"DEBUG - Unexpected error: {type(e).__name__} - {str(e)}")
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
