"""Shared Snowflake helpers: connection, temporary staging and audit logging."""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from dotenv import load_dotenv
from snowflake.connector.pandas_tools import write_pandas

load_dotenv()


def get_connection(schema: str = "RAW") -> snowflake.connector.SnowflakeConnection:
    """Connect as the pipeline service user using key-pair authentication."""
    key = serialization.load_pem_private_key(
        Path(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"]).read_bytes(), password=None
    )
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        private_key=key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ),
        role=os.getenv("SNOWFLAKE_ROLE", "ETF_TRANSFORMER"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", "ETF_WH"),
        database=os.getenv("SNOWFLAKE_DATABASE", "ETF_DB"),
        schema=schema,
        enable_server_session_keep_alive_auto_detection=False,
    )


def stage_dataframe(conn, df: pd.DataFrame, temp_table: str) -> None:
    """Load a DataFrame into a temporary table that disappears when the session ends."""
    write_pandas(conn, df, temp_table, auto_create_table=True,
                 table_type="temporary")


def log_run(conn, source: str, rows: int, status: str, message: str = "") -> None:
    """Write one row to LOAD_AUDIT describing this pipeline run."""
    conn.cursor().execute(
        "INSERT INTO LOAD_AUDIT VALUES (%s, %s, %s, %s, %s, %s)",
        (
            str(uuid.uuid4()),
            source,
            rows,
            status,
            message[:1000],
            datetime.now(timezone.utc).replace(tzinfo=None),
        ),
    )
