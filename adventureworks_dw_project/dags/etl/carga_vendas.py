from psycopg2.extras import execute_values

from etl.configuracoes import TAMANHO_LOTE
from etl.controle_incremental import executar_carga_incremental
from etl.extracao import COLUNAS_VENDAS, CONSULTA_VENDAS
from etl.transformacao import criar_datas


def criar_tabela_staging(conexao_destino):
    with conexao_destino.cursor() as cursor:
        cursor.execute(
            """
            CREATE TEMP TABLE IF NOT EXISTS stage_sales (
                sales_order_id INT,
                sales_order_detail_id INT,
                order_date DATE,
                product_id INT,
                customer_id INT,
                territory_id INT,
                salesperson_id INT,
                order_qty SMALLINT,
                unit_price NUMERIC(19,4),
                unit_price_discount NUMERIC(12,6),
                gross_amount NUMERIC(19,4),
                discount_amount NUMERIC(19,4),
                net_amount NUMERIC(19,4),
                estimated_cost NUMERIC(19,4),
                shipping_days INT,
                source_modified_at TIMESTAMP
            )
            ON COMMIT DROP
            """
        )


def validar_referencias(conexao_destino):
    with conexao_destino.cursor() as cursor:
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM stage_sales AS venda
            LEFT JOIN dw.dim_product AS produto
                ON produto.product_id = venda.product_id
            LEFT JOIN dw.dim_customer AS cliente
                ON cliente.customer_id = venda.customer_id
            LEFT JOIN dw.dim_territory AS territorio
                ON territorio.territory_id = venda.territory_id
            LEFT JOIN dw.dim_salesperson AS vendedor
                ON vendedor.salesperson_id = venda.salesperson_id
            WHERE produto.product_key IS NULL
               OR cliente.customer_key IS NULL
               OR territorio.territory_key IS NULL
               OR vendedor.salesperson_key IS NULL
            """
        )
        quantidade_sem_referencia = cursor.fetchone()[0]

    if quantidade_sem_referencia > 0:
        raise ValueError(
            f"{quantidade_sem_referencia} registros não possuem dimensões correspondentes."
        )


def inserir_vendas(conexao_destino):
    with conexao_destino.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO dw.fact_sales(
                sales_order_id,
                sales_order_detail_id,
                order_date_key,
                product_key,
                customer_key,
                territory_key,
                salesperson_key,
                order_qty,
                unit_price,
                unit_price_discount,
                gross_amount,
                discount_amount,
                net_amount,
                estimated_cost,
                shipping_days,
                source_modified_at
            )
            SELECT
                venda.sales_order_id,
                venda.sales_order_detail_id,
                data.date_key,
                produto.product_key,
                cliente.customer_key,
                territorio.territory_key,
                vendedor.salesperson_key,
                venda.order_qty,
                venda.unit_price,
                venda.unit_price_discount,
                venda.gross_amount,
                venda.discount_amount,
                venda.net_amount,
                venda.estimated_cost,
                venda.shipping_days,
                venda.source_modified_at
            FROM stage_sales AS venda
            INNER JOIN dw.dim_date AS data
                ON data.full_date = venda.order_date
            INNER JOIN dw.dim_product AS produto
                ON produto.product_id = venda.product_id
            INNER JOIN dw.dim_customer AS cliente
                ON cliente.customer_id = venda.customer_id
            INNER JOIN dw.dim_territory AS territorio
                ON territorio.territory_id = venda.territory_id
            INNER JOIN dw.dim_salesperson AS vendedor
                ON vendedor.salesperson_id = venda.salesperson_id
            ON CONFLICT(sales_order_id, sales_order_detail_id)
            DO UPDATE SET
                order_date_key = EXCLUDED.order_date_key,
                product_key = EXCLUDED.product_key,
                customer_key = EXCLUDED.customer_key,
                territory_key = EXCLUDED.territory_key,
                salesperson_key = EXCLUDED.salesperson_key,
                order_qty = EXCLUDED.order_qty,
                unit_price = EXCLUDED.unit_price,
                unit_price_discount = EXCLUDED.unit_price_discount,
                gross_amount = EXCLUDED.gross_amount,
                discount_amount = EXCLUDED.discount_amount,
                net_amount = EXCLUDED.net_amount,
                estimated_cost = EXCLUDED.estimated_cost,
                shipping_days = EXCLUDED.shipping_days,
                source_modified_at = EXCLUDED.source_modified_at
            """
        )


def processar_lote_vendas(conexao_destino, registros):
    criar_datas(conexao_destino, registros)
    criar_tabela_staging(conexao_destino)

    with conexao_destino.cursor() as cursor:
        execute_values(
            cursor,
            "INSERT INTO stage_sales VALUES %s",
            registros,
            page_size=TAMANHO_LOTE,
        )

    validar_referencias(conexao_destino)
    inserir_vendas(conexao_destino)

    with conexao_destino.cursor() as cursor:
        cursor.execute("TRUNCATE stage_sales")


def carregar_vendas():
    executar_carga_incremental(
        nome_pipeline="fact_sales",
        consulta_origem=CONSULTA_VENDAS,
        colunas=COLUNAS_VENDAS,
        chave_negocio="sales_order_id",
        processar_lote=processar_lote_vendas,
    )
