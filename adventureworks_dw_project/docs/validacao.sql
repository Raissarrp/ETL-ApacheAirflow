SELECT pipeline,last_modified,updated_at FROM ctl.watermark ORDER BY pipeline;
SELECT COUNT(*) AS linhas_fato,COUNT(DISTINCT sales_order_id) AS pedidos FROM dw.fact_sales;
SELECT COUNT(*) AS produtos FROM dw.dim_product;
SELECT COUNT(*) AS clientes FROM dw.dim_customer;
SELECT COUNT(*) AS territorios FROM dw.dim_territory;
SELECT COUNT(*) AS vendedores FROM dw.dim_salesperson;
SELECT sales_order_id,sales_order_detail_id,COUNT(*) FROM dw.fact_sales GROUP BY 1,2 HAVING COUNT(*)>1;
SELECT d.year,d.month,ROUND(SUM(f.net_amount),2) AS receita FROM dw.fact_sales f JOIN dw.dim_date d ON f.order_date_key=d.date_key GROUP BY 1,2 ORDER BY 1,2;
