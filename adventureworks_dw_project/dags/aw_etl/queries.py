"""Consultas à origem AdventureWorks no SQL Server."""
DIMENSIONS = {
 'product': ("""SELECT p.ProductID,p.Name,p.ProductNumber,psc.Name,pc.Name,p.StandardCost,p.ListPrice,
 (SELECT MAX(v) FROM (VALUES(p.ModifiedDate),(COALESCE(psc.ModifiedDate,CONVERT(datetime,'19000101'))),(COALESCE(pc.ModifiedDate,CONVERT(datetime,'19000101')))) AS vals(v)) AS modified_at
 FROM Production.Product p LEFT JOIN Production.ProductSubcategory psc ON p.ProductSubcategoryID=psc.ProductSubcategoryID
 LEFT JOIN Production.ProductCategory pc ON psc.ProductCategoryID=pc.ProductCategoryID""",
  ['product_id','product_name','product_number','subcategory','category','standard_cost','list_price','modified_at'],'product_id'),
 'customer': ("""SELECT c.CustomerID,COALESCE(NULLIF(LTRIM(RTRIM(CONCAT(p.FirstName,' ',p.LastName))),''),c.AccountNumber),c.AccountNumber,
 (SELECT MAX(v) FROM (VALUES(c.ModifiedDate),(COALESCE(p.ModifiedDate,CONVERT(datetime,'19000101')))) AS vals(v)) AS modified_at
 FROM Sales.Customer c LEFT JOIN Person.Person p ON c.PersonID=p.BusinessEntityID""",
  ['customer_id','customer_name','account_number','modified_at'],'customer_id'),
 'territory': ("""SELECT TerritoryID,Name,CountryRegionCode,[Group],ModifiedDate AS modified_at FROM Sales.SalesTerritory""",
  ['territory_id','territory_name','country_region_code','territory_group','modified_at'],'territory_id'),
 'salesperson': ("""SELECT sp.BusinessEntityID,COALESCE(NULLIF(LTRIM(RTRIM(CONCAT(p.FirstName,' ',p.LastName))),''),'Vendedor '+CAST(sp.BusinessEntityID AS varchar(20))),
 (SELECT MAX(v) FROM (VALUES(sp.ModifiedDate),(COALESCE(p.ModifiedDate,CONVERT(datetime,'19000101')))) AS vals(v)) AS modified_at
 FROM Sales.SalesPerson sp LEFT JOIN Person.Person p ON sp.BusinessEntityID=p.BusinessEntityID""",
  ['salesperson_id','salesperson_name','modified_at'],'salesperson_id'),
}
FACT_SQL = """
SELECT h.SalesOrderID,d.SalesOrderDetailID,CAST(h.OrderDate AS date),d.ProductID,COALESCE(h.CustomerID,-1),
 COALESCE(h.TerritoryID,-1),COALESCE(h.SalesPersonID,-1),d.OrderQty,d.UnitPrice,d.UnitPriceDiscount,
 CAST(d.OrderQty*d.UnitPrice AS decimal(19,4)),
 CAST(d.OrderQty*d.UnitPrice-d.LineTotal AS decimal(19,4)),d.LineTotal,
 CAST(d.OrderQty*p.StandardCost AS decimal(19,4)),
 CASE WHEN h.ShipDate IS NULL THEN NULL ELSE DATEDIFF(day,h.OrderDate,h.ShipDate) END,
 (SELECT MAX(v) FROM (VALUES(h.ModifiedDate),(d.ModifiedDate),(p.ModifiedDate)) AS vals(v)) AS modified_at
FROM Sales.SalesOrderHeader h
JOIN Sales.SalesOrderDetail d ON h.SalesOrderID=d.SalesOrderID
JOIN Production.Product p ON d.ProductID=p.ProductID
"""
FACT_COLS=['sales_order_id','sales_order_detail_id','order_date','product_id','customer_id','territory_id','salesperson_id','order_qty','unit_price','unit_price_discount','gross_amount','discount_amount','net_amount','estimated_cost','shipping_days','source_modified_at']
