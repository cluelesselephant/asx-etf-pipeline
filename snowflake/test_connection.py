"""Check that the service user can connect to Snowflake with its key pair."""
import os
from pathlib import Path

import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv

load_dotenv()

key = serialization.load_pem_private_key(
    Path(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]).read_bytes(), password=None
)
conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    private_key=key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ),
    role=os.environ["SNOWFLAKE_ROLE"],
    warehouse=os.environ["SNOWFLAKE_WAREHOUSE"],
    database=os.environ["SNOWFLAKE_DATABASE"],
    schema="RAW",
)
try:
    cur = conn.cursor()
    cur.execute(
        "SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE()")
    print("Connected as:", cur.fetchone())
    cur.execute("SHOW TABLES IN SCHEMA ETF_DB.RAW")
    print("Tables:", [row[1] for row in cur.fetchall()])
finally:
    conn.close()
