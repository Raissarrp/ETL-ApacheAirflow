"""Verificações após a carga."""
import logging
from .incremental import target_hook
LOG = logging.getLogger(__name__)

def quality_checks():
 with target_hook().get_conn() as conn:
  with conn.cursor() as c:
   c.execute('SELECT COUNT(*) FROM dw.fact_sales'); count=c.fetchone()[0]
   if not count: raise ValueError('Fact table is empty')
   c.execute('SELECT COUNT(*) FROM dw.fact_sales WHERE net_amount < 0 OR order_qty <= 0')
   if c.fetchone()[0]: raise ValueError('Invalid quantity or net amount')
   LOG.info('Data quality passed: %s fact lines',count)

