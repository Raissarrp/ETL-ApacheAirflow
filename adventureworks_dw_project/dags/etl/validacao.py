import logging

from etl.conexoes import obter_conexao_postgres


LOG = logging.getLogger(__name__)


def verificar_qualidade():
    conexao_destino = obter_conexao_postgres().get_conn()

    try:
        with conexao_destino.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM dw.fact_sales")
            quantidade_vendas = cursor.fetchone()[0]

            if quantidade_vendas == 0:
                raise ValueError("A tabela fato está vazia.")

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM dw.fact_sales
                WHERE net_amount < 0
                   OR order_qty <= 0
                """
            )
            quantidade_invalida = cursor.fetchone()[0]

            if quantidade_invalida > 0:
                raise ValueError(
                    "Existem vendas com quantidade ou valor líquido inválido."
                )

        LOG.info(
            "Validações concluídas: %d linhas na tabela fato.",
            quantidade_vendas,
        )
    finally:
        conexao_destino.close()
