import logging

from airflow.providers.microsoft.mssql.hooks.mssql import MsSqlHook
from airflow.providers.postgres.hooks.postgres import PostgresHook

from etl.configuracoes import CONEXAO_DESTINO, CONEXAO_ORIGEM


LOG = logging.getLogger(__name__)


def obter_conexao_sql_server():
    return MsSqlHook(mssql_conn_id=CONEXAO_ORIGEM)


def obter_conexao_postgres():
    return PostgresHook(postgres_conn_id=CONEXAO_DESTINO)


def verificar_conexoes():
    conexao_origem = obter_conexao_sql_server().get_conn()
    conexao_destino = obter_conexao_postgres().get_conn()

    try:
        cursor_origem = conexao_origem.cursor()
        try:
            cursor_origem.execute("SELECT 1")
            resultado_origem = cursor_origem.fetchone()
        finally:
            cursor_origem.close()

        cursor_destino = conexao_destino.cursor()
        try:
            cursor_destino.execute("SELECT 1")
            resultado_destino = cursor_destino.fetchone()
        finally:
            cursor_destino.close()

        if resultado_origem is None or resultado_origem[0] != 1:
            raise ValueError("O SQL Server não respondeu ao teste de conexão.")

        if resultado_destino is None or resultado_destino[0] != 1:
            raise ValueError("O PostgreSQL não respondeu ao teste de conexão.")

        LOG.info("Conexões com SQL Server e PostgreSQL aprovadas.")
    finally:
        conexao_origem.close()
        conexao_destino.close()


def validar_estruturas():
    conexao_destino = obter_conexao_postgres().get_conn()

    try:
        with conexao_destino.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema IN ('dw', 'ctl')
                """
            )
            tabelas = {
                f"{nome_schema}.{nome_tabela}"
                for nome_schema, nome_tabela in cursor.fetchall()
            }

        tabelas_obrigatorias = {
            "dw.dim_date",
            "dw.dim_product",
            "dw.dim_customer",
            "dw.dim_territory",
            "dw.dim_salesperson",
            "dw.fact_sales",
            "ctl.watermark",
        }
        tabelas_ausentes = sorted(tabelas_obrigatorias - tabelas)

        if tabelas_ausentes:
            raise ValueError(
                "Estruturas obrigatórias ausentes: "
                + ", ".join(tabelas_ausentes)
            )

        LOG.info("Estruturas do Data Warehouse encontradas.")
    finally:
        conexao_destino.close()
