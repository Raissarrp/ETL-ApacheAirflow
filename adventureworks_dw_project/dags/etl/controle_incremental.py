import logging
from datetime import datetime, timedelta

from psycopg2.extras import execute_values

from etl.configuracoes import DIAS_DE_SEGURANCA, TAMANHO_LOTE
from etl.conexoes import obter_conexao_postgres, obter_conexao_sql_server


LOG = logging.getLogger(__name__)
DATA_INICIAL = datetime(1900, 1, 1)


def consultar_watermark(conexao_destino, nome_pipeline):
    with conexao_destino.cursor() as cursor:
        cursor.execute(
            """
            SELECT last_modified
            FROM ctl.watermark
            WHERE pipeline = %s
            """,
            (nome_pipeline,),
        )
        resultado = cursor.fetchone()

    if resultado is None:
        return DATA_INICIAL

    return resultado[0]


def atualizar_watermark(conexao_destino, nome_pipeline, ultima_data):
    with conexao_destino.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ctl.watermark(pipeline, last_modified)
            VALUES (%s, %s)
            ON CONFLICT(pipeline)
            DO UPDATE SET
                last_modified = GREATEST(
                    ctl.watermark.last_modified,
                    EXCLUDED.last_modified
                ),
                updated_at = now()
            """,
            (nome_pipeline, ultima_data),
        )


def atualizar_dimensao(
    conexao_destino,
    nome_dimensao,
    colunas,
    chave_negocio,
    registros,
):
    nomes_colunas = ",".join(colunas)
    atualizacoes = ",".join(
        f"{coluna}=EXCLUDED.{coluna}"
        for coluna in colunas
        if coluna != chave_negocio
    )
    consulta_upsert = (
        f"INSERT INTO dw.dim_{nome_dimensao} "
        f"({nomes_colunas}) VALUES %s "
        f"ON CONFLICT ({chave_negocio}) "
        f"DO UPDATE SET {atualizacoes}"
    )

    with conexao_destino.cursor() as cursor:
        execute_values(
            cursor,
            consulta_upsert,
            registros,
            page_size=TAMANHO_LOTE,
        )


def executar_carga_incremental(
    nome_pipeline,
    consulta_origem,
    colunas,
    chave_negocio,
    processar_lote=None,
):
    conexao_origem = obter_conexao_sql_server().get_conn()
    conexao_destino = obter_conexao_postgres().get_conn()

    try:
        conexao_destino.autocommit = False

        ultima_data = consultar_watermark(conexao_destino, nome_pipeline)
        data_inicial = ultima_data - timedelta(days=DIAS_DE_SEGURANCA)

        cursor_origem = conexao_origem.cursor()
        cursor_origem.execute("SELECT GETDATE()")
        data_limite = cursor_origem.fetchone()[0]

        cursor_origem.execute(
            f"""
            SELECT *
            FROM ({consulta_origem}) AS registros_alterados
            WHERE modified_at >= %s
              AND modified_at <= %s
            """,
            (data_inicial, data_limite),
        )

        quantidade_processada = 0

        while True:
            registros = cursor_origem.fetchmany(TAMANHO_LOTE)
            if not registros:
                break

            if processar_lote is None:
                atualizar_dimensao(
                    conexao_destino,
                    nome_pipeline,
                    colunas,
                    chave_negocio,
                    registros,
                )
            else:
                processar_lote(conexao_destino, registros)

            quantidade_processada += len(registros)

        atualizar_watermark(conexao_destino, nome_pipeline, data_limite)
        conexao_destino.commit()
        cursor_origem.close()

        LOG.info(
            "%s processou %d registros até %s",
            nome_pipeline,
            quantidade_processada,
            data_limite,
        )
    except Exception:
        conexao_destino.rollback()
        raise
    finally:
        conexao_origem.close()
        conexao_destino.close()
