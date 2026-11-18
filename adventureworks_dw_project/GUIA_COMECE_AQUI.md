# Guia simples — AdventureWorks DW

## O que acontece?

SQL Server (AdventureWorks) → Airflow (DAG) → PostgreSQL (Star Schema) → SQL (10 KPIs).

O Airflow **não é um banco**: ele agenda e executa as tarefas e lê as credenciais cadastradas em **Admin > Connections**.

## Ordem de execução

1. Confirme que o AdventureWorks2016 está acessível no SQL Server.
2. Crie um banco PostgreSQL de destino vazio e execute `sql/01_schema.sql` nele.
3. Instale os providers `apache-airflow-providers-microsoft-mssql` e `apache-airflow-providers-postgres` em versões compatíveis com seu Airflow.
4. Em **Admin > Connections**, crie:
   - `adventureworks_mssql`: tipo **Microsoft SQL Server**, host, porta, usuário, senha, schema/database `AdventureWorks2016`.
   - `adventureworks_postgres`: tipo **Postgres**, host, porta, usuário, senha, schema/database do DW.
5. Copie **toda a pasta `dags/`**, inclusive `aw_etl/`, para o diretório de DAGs do Airflow.
6. Confira se a DAG `adventureworks_star_incremental` aparece sem erros de importação. Acione uma execução manual.
7. Verifique `docs/validacao.sql` e depois execute `sql/02_kpis.sql`.
8. Capture prints reais do Graph e dos resultados e insira no artigo; publique o repositório e informe o link.

**Atenção:** se o Airflow estiver em Docker, `localhost` na Connection aponta para o próprio contêiner, não para o SQL Server/PostgreSQL do Windows. Configure host acessível a partir do contêiner.

## Arquivos Python

- `dags/adventureworks_dw.py`: define ordem e agendamento.
- `dags/aw_etl/config.py`: IDs de conexão e tamanho de lotes, sem credenciais.
- `dags/aw_etl/queries.py`: SQL de extração de dimensões e vendas.
- `dags/aw_etl/incremental.py`: hooks, watermark, lotes e upsert.
- `dags/aw_etl/fact.py`: carrega fatos e relaciona dimensões.
- `dags/aw_etl/quality.py`: valida o resultado.

## Incremental em palavras simples

A tabela `ctl.watermark` guarda a última data processada por etapa. A cada execução, o Airflow busca dados modificados desde essa data (com uma margem de dois dias), atualiza linhas existentes e insere novas linhas. Só avança o watermark após commit bem-sucedido. **Limitação:** exclusões físicas na origem não são capturadas e mudanças retroativas sem atualização de `ModifiedDate` podem passar despercebidas.

## Observações de validação

Os arquivos foram verificados sintaticamente; não houve execução ponta a ponta contra seus bancos. Os prints, resultados reais e formatação final do artigo devem ser confirmados no seu ambiente.
