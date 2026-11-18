DIMENSOES = {
    "product": (
        """
        SELECT
            produto.ProductID,
            produto.Name,
            produto.ProductNumber,
            subcategoria.Name,
            categoria.Name,
            produto.StandardCost,
            produto.ListPrice,
            (
                SELECT MAX(valor_modificacao)
                FROM (
                    VALUES
                        (produto.ModifiedDate),
                        (COALESCE(subcategoria.ModifiedDate, CONVERT(datetime, '19000101'))),
                        (COALESCE(categoria.ModifiedDate, CONVERT(datetime, '19000101')))
                ) AS modificacoes(valor_modificacao)
            ) AS modified_at
        FROM Production.Product AS produto
        LEFT JOIN Production.ProductSubcategory AS subcategoria
            ON produto.ProductSubcategoryID = subcategoria.ProductSubcategoryID
        LEFT JOIN Production.ProductCategory AS categoria
            ON subcategoria.ProductCategoryID = categoria.ProductCategoryID
        """,
        [
            "product_id",
            "product_name",
            "product_number",
            "subcategory",
            "category",
            "standard_cost",
            "list_price",
            "modified_at",
        ],
        "product_id",
    ),
    "customer": (
        """
        SELECT
            cliente.CustomerID,
            COALESCE(
                NULLIF(
                    LTRIM(RTRIM(CONCAT(pessoa.FirstName, ' ', pessoa.LastName))),
                    ''
                ),
                cliente.AccountNumber
            ),
            cliente.AccountNumber,
            (
                SELECT MAX(valor_modificacao)
                FROM (
                    VALUES
                        (cliente.ModifiedDate),
                        (COALESCE(pessoa.ModifiedDate, CONVERT(datetime, '19000101')))
                ) AS modificacoes(valor_modificacao)
            ) AS modified_at
        FROM Sales.Customer AS cliente
        LEFT JOIN Person.Person AS pessoa
            ON cliente.PersonID = pessoa.BusinessEntityID
        """,
        [
            "customer_id",
            "customer_name",
            "account_number",
            "modified_at",
        ],
        "customer_id",
    ),
    "territory": (
        """
        SELECT
            TerritoryID,
            Name,
            CountryRegionCode,
            [Group],
            ModifiedDate AS modified_at
        FROM Sales.SalesTerritory
        """,
        [
            "territory_id",
            "territory_name",
            "country_region_code",
            "territory_group",
            "modified_at",
        ],
        "territory_id",
    ),
    "salesperson": (
        """
        SELECT
            vendedor.BusinessEntityID,
            COALESCE(
                NULLIF(
                    LTRIM(RTRIM(CONCAT(pessoa.FirstName, ' ', pessoa.LastName))),
                    ''
                ),
                'Vendedor ' + CAST(vendedor.BusinessEntityID AS varchar(20))
            ),
            (
                SELECT MAX(valor_modificacao)
                FROM (
                    VALUES
                        (vendedor.ModifiedDate),
                        (COALESCE(pessoa.ModifiedDate, CONVERT(datetime, '19000101')))
                ) AS modificacoes(valor_modificacao)
            ) AS modified_at
        FROM Sales.SalesPerson AS vendedor
        LEFT JOIN Person.Person AS pessoa
            ON vendedor.BusinessEntityID = pessoa.BusinessEntityID
        """,
        [
            "salesperson_id",
            "salesperson_name",
            "modified_at",
        ],
        "salesperson_id",
    ),
}

CONSULTA_VENDAS = """
SELECT
    pedido.SalesOrderID,
    detalhe.SalesOrderDetailID,
    CAST(pedido.OrderDate AS date),
    detalhe.ProductID,
    COALESCE(pedido.CustomerID, -1),
    COALESCE(pedido.TerritoryID, -1),
    COALESCE(pedido.SalesPersonID, -1),
    detalhe.OrderQty,
    detalhe.UnitPrice,
    detalhe.UnitPriceDiscount,
    CAST(detalhe.OrderQty * detalhe.UnitPrice AS decimal(19,4)),
    CAST(
        detalhe.OrderQty * detalhe.UnitPrice - detalhe.LineTotal
        AS decimal(19,4)
    ),
    detalhe.LineTotal,
    CAST(detalhe.OrderQty * produto.StandardCost AS decimal(19,4)),
    CASE
        WHEN pedido.ShipDate IS NULL THEN NULL
        ELSE DATEDIFF(day, pedido.OrderDate, pedido.ShipDate)
    END,
    (
        SELECT MAX(valor_modificacao)
        FROM (
            VALUES
                (pedido.ModifiedDate),
                (detalhe.ModifiedDate),
                (produto.ModifiedDate)
        ) AS modificacoes(valor_modificacao)
    ) AS modified_at
FROM Sales.SalesOrderHeader AS pedido
INNER JOIN Sales.SalesOrderDetail AS detalhe
    ON pedido.SalesOrderID = detalhe.SalesOrderID
INNER JOIN Production.Product AS produto
    ON detalhe.ProductID = produto.ProductID
"""

COLUNAS_VENDAS = [
    "sales_order_id",
    "sales_order_detail_id",
    "order_date",
    "product_id",
    "customer_id",
    "territory_id",
    "salesperson_id",
    "order_qty",
    "unit_price",
    "unit_price_discount",
    "gross_amount",
    "discount_amount",
    "net_amount",
    "estimated_cost",
    "shipping_days",
    "source_modified_at",
]
