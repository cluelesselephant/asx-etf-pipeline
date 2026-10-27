"""Create (or reuse) an RSA key pair for the Snowflake service user.

The keys are saved outside the project folder so they can never be committed.
Running this again reuses the existing key and reprints the ALTER USER line.
"""
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

key_dir = Path.home() / ".snowflake"
key_dir.mkdir(exist_ok=True)
private_path = key_dir / "rsa_key.p8"
public_path = key_dir / "rsa_key.pub"

if private_path.exists():
    key = serialization.load_pem_private_key(
        private_path.read_bytes(), password=None)
    print(f"Using existing private key at {private_path}")
else:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_path.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ))
    print(f"Created new private key at {private_path} (never share this file)")

public_pem = key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo,
)
public_path.write_bytes(public_pem)

body = "".join(line for line in public_pem.decode().splitlines()
               if "-----" not in line)
print("\nRun this in a Snowflake worksheet as ACCOUNTADMIN:\n")
print(f"ALTER USER ETF_PIPELINE_SVC SET RSA_PUBLIC_KEY='{body}';")
