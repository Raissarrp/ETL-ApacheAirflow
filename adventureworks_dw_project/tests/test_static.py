from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
dag_source = (root / "dags/dag_adventureworks.py").read_text()
incremental_source = (root / "dags/etl/controle_incremental.py").read_text()
fact_source = (root / "dags/etl/carga_vendas.py").read_text()

ast.parse(dag_source)
ast.parse(incremental_source)
ast.parse(fact_source)
conexoes_source = (root / "dags/etl/conexoes.py").read_text()
assert "MsSqlHook" in conexoes_source
assert "PostgresHook" in conexoes_source
assert 'mssql_conn_id=CONEXAO_ORIGEM' in conexoes_source
assert 'postgres_conn_id=CONEXAO_DESTINO' in conexoes_source
assert "ON CONFLICT" in incremental_source
assert "last_modified" in incremental_source
assert "password=" not in incremental_source.lower()
assert "verify_connections" in dag_source
assert "validate_structures" in dag_source
assert "aw_etl" not in dag_source
assert "adventureworks_dw.py" not in dag_source

kpis = (root / "sql/indicadores.sql").read_text()
assert kpis.count(";") == 10
print("Testes estáticos aprovados.")
