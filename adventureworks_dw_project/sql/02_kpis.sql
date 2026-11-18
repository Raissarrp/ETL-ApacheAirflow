-- 01 Receita líquida
SELECT ROUND(SUM(net_amount),2) AS receita_liquida FROM dw.fact_sales;
-- 02 Quantidade de pedidos distintos
SELECT COUNT(DISTINCT sales_order_id) AS pedidos FROM dw.fact_sales;
-- 03 Quantidade de itens vendidos
SELECT SUM(order_qty) AS unidades FROM dw.fact_sales;
-- 04 Ticket médio por pedido (não por linha)
SELECT ROUND(SUM(net_amount)/NULLIF(COUNT(DISTINCT sales_order_id),0),2) AS ticket_medio FROM dw.fact_sales;
-- 05 Margem bruta estimada: custo padrão atual, não custo contábil histórico
SELECT ROUND(100*SUM(net_amount-estimated_cost)/NULLIF(SUM(net_amount),0),2) AS margem_estimada_pct FROM dw.fact_sales WHERE estimated_cost IS NOT NULL;
-- 06 Desconto sobre valor bruto
SELECT ROUND(100*SUM(discount_amount)/NULLIF(SUM(gross_amount),0),2) AS desconto_pct FROM dw.fact_sales;
-- 07 Receita por território
SELECT t.territory_name,ROUND(SUM(f.net_amount),2) AS receita FROM dw.fact_sales f JOIN dw.dim_territory t USING(territory_key) GROUP BY t.territory_name ORDER BY receita DESC;
-- 08 Top 10 produtos por receita
SELECT p.product_name,ROUND(SUM(f.net_amount),2) AS receita FROM dw.fact_sales f JOIN dw.dim_product p USING(product_key) GROUP BY p.product_key,p.product_name ORDER BY receita DESC LIMIT 10;
-- 09 Crescimento mensal de receita (%)
WITH m AS (SELECT d.year,d.month,MAKE_DATE(d.year,d.month,1) AS mes,SUM(f.net_amount) AS receita FROM dw.fact_sales f JOIN dw.dim_date d ON f.order_date_key=d.date_key GROUP BY 1,2), c AS (SELECT mes,receita,LAG(receita) OVER(ORDER BY mes) AS anterior FROM m) SELECT mes,ROUND(receita,2) AS receita,ROUND(100*(receita-anterior)/NULLIF(anterior,0),2) AS crescimento_pct FROM c ORDER BY mes;
-- 10 Prazo médio de envio em dias, ponderado por linhas de pedido (não por pedidos)
SELECT ROUND(AVG(shipping_days::NUMERIC),2) AS dias_medios FROM dw.fact_sales WHERE shipping_days IS NOT NULL;
