"""Conexões via Airflow, controle incremental e upsert das dimensões."""
from datetime import datetime, timedelta
import logging
from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import execute_values
from .config import SOURCE_CONN_ID, TARGET_CONN_ID, LOOKBACK_DAYS, BATCH_SIZE
from .queries import DIMENSIONS
LOG = logging.getLogger(__name__)

def source_hook():
    return MsSqlHook(mssql_conn_id=SOURCE_CONN_ID)
def target_hook():
    return PostgresHook(postgres_conn_id=TARGET_CONN_ID)

def verify_connections():
    src = source_hook().get_conn()
    dst = target_hook().get_conn()
    try:
        cursor = src.cursor()
        try:
            cursor.execute("SELECT 1")
            if cursor.fetchone()[0] != 1:
                raise ValueError("SQL Server did not answer the connection test")
        finally:
            cursor.close()
        cursor = dst.cursor()
        try:
            cursor.execute("SELECT 1")
            if cursor.fetchone()[0] != 1:
                raise ValueError("PostgreSQL did not answer the connection test")
        finally:
            cursor.close()
        LOG.info("Both database connections passed")
    finally:
        src.close()
        dst.close()

def validate_structures():
    with target_hook().get_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('dw', 'ctl')
            """)
            tables = {f"{schema}.{table}" for schema, table in cursor.fetchall()}
            required = {
                "dw.dim_date", "dw.dim_product", "dw.dim_customer",
                "dw.dim_territory", "dw.dim_salesperson", "dw.fact_sales",
                "ctl.watermark",
            }
            missing = sorted(required - tables)
            if missing:
                raise ValueError(
                    "Missing required Data Warehouse structures: " + ", ".join(missing)
                )
            LOG.info("Required Data Warehouse structures are present")

def watermark(conn, name):
 with conn.cursor() as c:
  c.execute('SELECT last_modified FROM ctl.watermark WHERE pipeline=%s',(name,))
  row=c.fetchone()
 return row[0] if row else datetime(1900,1,1)

def update_watermark(conn,name,upper):
 with conn.cursor() as c:
  c.execute('INSERT INTO ctl.watermark(pipeline,last_modified) VALUES(%s,%s) ON CONFLICT(pipeline) DO UPDATE SET last_modified=GREATEST(ctl.watermark.last_modified,EXCLUDED.last_modified),updated_at=now()',(name,upper))

def run_incremental(name, base_sql, columns, conflict, transform=None):
 src=source_hook().get_conn(); dst=target_hook().get_conn()
 try:
  dst.autocommit=False
  low=watermark(dst,name)-timedelta(days=LOOKBACK_DAYS)
  sc=src.cursor(); sc.execute('SELECT GETDATE()'); upper=sc.fetchone()[0]
  # Apply watermark to the source query, not a local Python filter.
  sc.execute(f'SELECT * FROM ({base_sql}) AS changes WHERE modified_at >= %s AND modified_at <= %s',(low,upper))
  count=0
  while True:
   rows=sc.fetchmany(BATCH_SIZE)
   if not rows: break
   if transform: transform(dst,rows)
   else:
    fields=','.join(columns)
    updates=','.join(f'{c}=EXCLUDED.{c}' for c in columns if c!=conflict)
    sql=f'INSERT INTO dw.dim_{name} ({fields}) VALUES %s ON CONFLICT ({conflict}) DO UPDATE SET {updates}'
    with dst.cursor() as cur: execute_values(cur,sql,rows,page_size=BATCH_SIZE)
   count+=len(rows)
  update_watermark(dst,name,upper)
  dst.commit(); LOG.info('%s processed %d source records through %s',name,count,upper)
 except Exception:
  dst.rollback(); raise
 finally:
  src.close(); dst.close()

def load_dimension(name):
 query,cols,key=DIMENSIONS[name]
 run_incremental(name,query,cols,key)

