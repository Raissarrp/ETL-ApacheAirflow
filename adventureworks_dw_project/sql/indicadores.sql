SELECT ROUND(SUM(net_amount), 2) AS receita_liquida
FROM dw.fact_sales;

SELECT ROUND(
    SUM(net_amount) / NULLIF(COUNT(DISTINCT sales_order_id), 0),
    2
) AS ticket_medio
FROM dw.fact_sales;

SELECT SUM(order_qty) AS unidades
FROM dw.fact_sales;

SELECT ROUND(
    100 * SUM(net_amount - estimated_cost)
        / NULLIF(SUM(net_amount), 0),
    2
) AS margem_estimada_pct
FROM dw.fact_sales
WHERE estimated_cost IS NOT NULL;

SELECT ROUND(
    100 * SUM(discount_amount)
        / NULLIF(SUM(gross_amount), 0),
    2
) AS desconto_pct
FROM dw.fact_sales;

SELECT
    territorio.territory_name,
    ROUND(SUM(venda.net_amount), 2) AS receita
FROM dw.fact_sales AS venda
INNER JOIN dw.dim_territory AS territorio
    USING(territory_key)
GROUP BY territorio.territory_name
ORDER BY receita DESC;

SELECT
    produto.product_name,
    ROUND(SUM(venda.net_amount), 2) AS receita
FROM dw.fact_sales AS venda
INNER JOIN dw.dim_product AS produto
    USING(product_key)
GROUP BY produto.product_key, produto.product_name
ORDER BY receita DESC
LIMIT 10;

SELECT
    vendedor.salesperson_name,
    ROUND(SUM(venda.net_amount), 2) AS receita
FROM dw.fact_sales AS venda
INNER JOIN dw.dim_salesperson AS vendedor
    USING(salesperson_key)
GROUP BY vendedor.salesperson_key, vendedor.salesperson_name
ORDER BY receita DESC;

WITH vendas_mensais AS (
    SELECT
        data.year,
        data.month,
        MAKE_DATE(data.year, data.month, 1) AS mes,
        SUM(venda.net_amount) AS receita
    FROM dw.fact_sales AS venda
    INNER JOIN dw.dim_date AS data
        ON venda.order_date_key = data.date_key
    GROUP BY data.year, data.month
),
vendas_com_anterior AS (
    SELECT
        mes,
        receita,
        LAG(receita) OVER(ORDER BY mes) AS receita_anterior
    FROM vendas_mensais
)
SELECT
    mes,
    ROUND(receita, 2) AS receita,
    ROUND(
        100 * (receita - receita_anterior)
            / NULLIF(receita_anterior, 0),
        2
    ) AS crescimento_pct
FROM vendas_com_anterior
ORDER BY mes;

SELECT ROUND(
    AVG(shipping_days::NUMERIC),
    2
) AS dias_medios
FROM dw.fact_sales
WHERE shipping_days IS NOT NULL;
