SELECT pipeline, last_modified, updated_at
FROM ctl.watermark
ORDER BY pipeline;

SELECT
    COUNT(*) AS linhas_fato,
    COUNT(DISTINCT sales_order_id) AS pedidos
FROM dw.fact_sales;

SELECT COUNT(*) AS produtos FROM dw.dim_product;
SELECT COUNT(*) AS clientes FROM dw.dim_customer;
SELECT COUNT(*) AS territorios FROM dw.dim_territory;
SELECT COUNT(*) AS vendedores FROM dw.dim_salesperson;

SELECT
    sales_order_id,
    sales_order_detail_id,
    COUNT(*)
FROM dw.fact_sales
GROUP BY sales_order_id, sales_order_detail_id
HAVING COUNT(*) > 1;

SELECT
    data.year,
    data.month,
    ROUND(SUM(venda.net_amount), 2) AS receita
FROM dw.fact_sales AS venda
INNER JOIN dw.dim_date AS data
    ON venda.order_date_key = data.date_key
GROUP BY data.year, data.month
ORDER BY data.year, data.month;
