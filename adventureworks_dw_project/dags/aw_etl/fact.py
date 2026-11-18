"""Carga da tabela fato e resolução das chaves dimensionais."""
from psycopg2.extras import execute_values
from .config import BATCH_SIZE
from .queries import FACT_SQL, FACT_COLS
from .incremental import run_incremental

def load_fact():
 def insert_fact(dst,rows):
  dates=sorted(set(r[2] for r in rows))
  with dst.cursor() as c:
   execute_values(c,"""INSERT INTO dw.dim_date(date_key,full_date,year,quarter,month,month_name,day)
    VALUES %s ON CONFLICT(date_key) DO NOTHING""",[(int(d.strftime('%Y%m%d')),d,d.year,(d.month-1)//3+1,d.month,d.strftime('%B'),d.day) for d in dates])
   # Resolve surrogate keys in PostgreSQL (not Python); fail transaction if any reference is missing.
   c.execute("""CREATE TEMP TABLE IF NOT EXISTS stage_sales (
    sales_order_id INT,sales_order_detail_id INT,order_date DATE,product_id INT,customer_id INT,
    territory_id INT,salesperson_id INT,order_qty SMALLINT,unit_price NUMERIC(19,4),unit_price_discount NUMERIC(12,6),
    gross_amount NUMERIC(19,4),discount_amount NUMERIC(19,4),net_amount NUMERIC(19,4),estimated_cost NUMERIC(19,4),
    shipping_days INT,source_modified_at TIMESTAMP) ON COMMIT DROP""")
   execute_values(c,'INSERT INTO stage_sales VALUES %s',rows,page_size=BATCH_SIZE)
   c.execute("""SELECT COUNT(*) FROM stage_sales s
    LEFT JOIN dw.dim_product p ON p.product_id=s.product_id
    LEFT JOIN dw.dim_customer cu ON cu.customer_id=s.customer_id
    LEFT JOIN dw.dim_territory t ON t.territory_id=s.territory_id
    LEFT JOIN dw.dim_salesperson sp ON sp.salesperson_id=s.salesperson_id
    WHERE p.product_key IS NULL OR cu.customer_key IS NULL OR t.territory_key IS NULL OR sp.salesperson_key IS NULL""")
   missing=c.fetchone()[0]
   if missing: raise ValueError(f'{missing} fact rows lack dimension references; check dimension sync')
   c.execute("""INSERT INTO dw.fact_sales(sales_order_id,sales_order_detail_id,order_date_key,product_key,customer_key,territory_key,salesperson_key,order_qty,unit_price,unit_price_discount,gross_amount,discount_amount,net_amount,estimated_cost,shipping_days,source_modified_at)
    SELECT s.sales_order_id,s.sales_order_detail_id,dt.date_key,p.product_key,cu.customer_key,t.territory_key,sp.salesperson_key,s.order_qty,s.unit_price,s.unit_price_discount,s.gross_amount,s.discount_amount,s.net_amount,s.estimated_cost,s.shipping_days,s.source_modified_at
    FROM stage_sales s JOIN dw.dim_date dt ON dt.full_date=s.order_date
    JOIN dw.dim_product p ON p.product_id=s.product_id JOIN dw.dim_customer cu ON cu.customer_id=s.customer_id
    JOIN dw.dim_territory t ON t.territory_id=s.territory_id JOIN dw.dim_salesperson sp ON sp.salesperson_id=s.salesperson_id
    ON CONFLICT(sales_order_id,sales_order_detail_id) DO UPDATE SET
     order_date_key=EXCLUDED.order_date_key,product_key=EXCLUDED.product_key,customer_key=EXCLUDED.customer_key,
     territory_key=EXCLUDED.territory_key,salesperson_key=EXCLUDED.salesperson_key,order_qty=EXCLUDED.order_qty,
     unit_price=EXCLUDED.unit_price,unit_price_discount=EXCLUDED.unit_price_discount,gross_amount=EXCLUDED.gross_amount,
     discount_amount=EXCLUDED.discount_amount,net_amount=EXCLUDED.net_amount,estimated_cost=EXCLUDED.estimated_cost,
     shipping_days=EXCLUDED.shipping_days,source_modified_at=EXCLUDED.source_modified_at""")
   c.execute('TRUNCATE stage_sales')
 run_incremental('fact_sales',FACT_SQL,FACT_COLS,'sales_order_id',insert_fact)

