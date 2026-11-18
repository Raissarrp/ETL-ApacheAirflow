# Dicionário e modelagem

**Grão:** uma linha de `Sales.SalesOrderDetail` por (`SalesOrderID`, `SalesOrderDetailID`).

| Tabela | Chave | Atributos | Fonte |
|---|---|---|---|
| dim_date | date_key (YYYYMMDD) | full_date, year, quarter, month, month_name, day | SalesOrderHeader.OrderDate |
| dim_product | product_key (substituta) | product_id, product_name, category, subcategory, standard_cost, list_price | Production.Product, ProductSubcategory, ProductCategory |
| dim_customer | customer_key (substituta) | customer_id, customer_name, account_number | Sales.Customer, Person.Person |
| dim_territory | territory_key (substituta) | territory_id, territory_name, country_region_code, territory_group | Sales.SalesTerritory |
| dim_salesperson | salesperson_key (substituta) | salesperson_id, salesperson_name | Sales.SalesPerson, Person.Person |
| fact_sales | (sales_order_id,sales_order_detail_id) | cinco FKs, order_qty, unit_price, discount_amount, net_amount, estimated_cost, shipping_days | SalesOrderHeader, SalesOrderDetail, Product |
| ctl.watermark | pipeline | last_modified, updated_at | Controle incremental |

`gross_amount=OrderQty×UnitPrice`, `discount_amount=gross_amount−LineTotal`, `net_amount=LineTotal`, `estimated_cost=OrderQty×StandardCost`, `shipping_days=DATEDIFF(day,OrderDate,ShipDate)`.

A modelagem desnormaliza categorias e pessoas nas dimensões; nenhuma dimensão depende de outra dimensão, caracterizando Star Schema. Dimensões SCD tipo 1. Custo padrão representa aproximação da margem e pode ser alterado retrospectivamente.
