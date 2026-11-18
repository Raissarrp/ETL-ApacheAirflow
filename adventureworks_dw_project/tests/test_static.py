from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
dag_source = (root / "dags/adventureworks_dw.py").read_text()
incremental_source = (root / "dags/aw_etl/incremental.py").read_text()
fact_source = (root / "dags/aw_etl/fact.py").read_text()

ast.parse(dag_source)
ast.parse(incremental_source)
ast.parse(fact_source)
assert "MsSqlHook" in incremental_source
assert "PostgresHook" in incremental_source
assert "mssql_conn_id=SOURCE_CONN_ID" in incremental_source
assert "postgres_conn_id=TARGET_CONN_ID" in incremental_source
assert "ON CONFLICT" in incremental_source
assert "last_modified" in incremental_source
assert "password=" not in incremental_source.lower()
assert "verify_connections" in dag_source
assert "validate_structures" in dag_source

kpis = (root / "sql/02_kpis.sql").read_text()
assert len([line for line in kpis.splitlines() if line.startswith("-- ")]) == 10
print("Testes estáticos aprovados.")
