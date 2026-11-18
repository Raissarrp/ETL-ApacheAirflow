# AdventureWorks — Data Warehouse Star Schema + Airflow

Projeto individual: SQL Server AdventureWorks2016 → Apache Airflow → PostgreSQL (DW).

## Configuração atual deste workspace

- Airflow: 3.1.8
- Metadados: PostgreSQL 16 no Docker Compose
- Data Warehouse: banco separado `adventureworks_dw` no mesmo PostgreSQL do Compose
- Interface: http://localhost:8080
- Usuário local padrão: `airflow`
- Connection PostgreSQL já cadastrada por CLI como `adventureworks_postgres`
- Host da Connection PostgreSQL dentro do Docker: `postgres`
- Porta: `5432`
- Banco: `adventureworks_dw`

O SQL Server de origem não foi detectado nesta máquina (porta 1433 indisponível). Cadastre `adventureworks_mssql` no painel do Airflow com o host real acessível pelo contêiner.
Use `host.docker.internal` para um SQL Server instalado no Windows quando houver conectividade.

## Pré-requisitos

- SQL Server com o banco **AdventureWorks2016** restaurado e usuário de leitura.
- PostgreSQL 14+ com um banco de destino criado e usuário com privilégios para criar schemas/tabelas.
- Apache Airflow 2.9–2.10 com providers `apache-airflow-providers-microsoft-mssql` e `apache-airflow-providers-postgres`, compatíveis com a versão do Airflow.
- Driver de conexão SQL Server suportado pelo provider (`pymssql` para MsSqlHook).

## Configuração obrigatória: Airflow Admin → Connections

Crie as conexões **na interface do Airflow**, sem incluir credenciais no código:

| Connection Id | Connection Type | Campos |
|---|---|---|
| `adventureworks_mssql` | Microsoft SQL Server | Host, Schema=`AdventureWorks2016`, Login, Password, Port=1433 |
| `adventureworks_postgres` | Postgres | Host, Database/Schema=seu banco DW, Login, Password, Port=5432 |

Se o tipo Microsoft SQL Server não aparecer, instale o provider e reinicie o Airflow. Para ambiente Docker, `localhost` dentro do container NÃO aponta para seu computador; use nome do serviço Docker ou `host.docker.internal` conforme a rede.

## Instalação

1. Execute `sql/01_schema.sql` **uma única vez no PostgreSQL de destino** (psql, DBeaver ou pgAdmin).
2. Copie `dags/adventureworks_dw.py` para a pasta `dags/` reconhecida pelo Airflow.
3. Instale os providers no **mesmo ambiente Python** do scheduler e workers, e reinicie serviços.
4. Crie as duas Connections pelo painel **Admin → Connections**.
5. No painel DAGs, ative `adventureworks_star_incremental` e execute **Trigger DAG**.
6. Verifique `load_dim_*` → `load_fact_sales` → `quality_checks` e os logs.
7. Execute `sql/02_kpis.sql` no PostgreSQL para obter os dez resultados.
8. Faça uma segunda execução sem alterações e confira o número de linhas processadas nos logs (janela de reprocessamento de dois dias).

**Importante:** o primeiro processamento histórico pode levar tempo e requer acesso ao SQL Server. O projeto não contém o backup AdventureWorks, nem credenciais, nem prints fabricados.

## Incrementalidade

Cada dimensão e a fato têm watermark próprio em `ctl.watermark`. A consulta filtra `modified_at` no SQL Server por `last_modified - 2 dias` até `GETDATE()` e usa `ON CONFLICT DO UPDATE` no PostgreSQL. O watermark avança **na mesma transação** dos registros. Em caso de falha, rollback impede avançar o marcador. A janela de dois dias cobre atualizações tardias comuns, mas não garante eventos retroativos anteriores à janela.

**Limitações documentadas:** exclusões físicas na origem não são detectadas; use CDC/Change Tracking para isso. A dimensão é Tipo 1, sem histórico de atributos; a margem utiliza `StandardCost` da origem e é **estimativa**, não margem contábil. A medida de prazo de envio é média por linha de pedido. Alterações no custo padrão disparam recálculo das linhas do produto enquanto `ModifiedDate` do produto é atualizado. Não há garantia de snapshot transacional único entre dimensões e fatos.

## Evidências para o artigo

- Captura da DAG no Grid/Graph e captura do resultado de cada task.
- Captura de `SELECT * FROM ctl.watermark;` após duas execuções.
- Captura dos resultados reais das 10 consultas SQL.
- Diagrama `diagrams/star_schema.puml` (abrir no PlantUML).
- Publique no GitHub e substitua `[URL_DO_REPOSITORIO]` no artigo.

## Estrutura

- `dags/`: pipeline Airflow com hooks e IDs de conexão.
- `sql/`: DDL e 10 indicadores.
- `diagrams/`: diagrama estrela em PlantUML.
- `article/`: artigo editável (modelo, completar evidências e resultados).
- `tests/`: testes estáticos de estrutura.
- `docs/`: dicionário e roteiro de validação.

## Segurança

Não comite `.env`, senhas, backups nem exports de Connections. Configure permissões mínimas: origem somente leitura, destino com permissões sobre `dw` e `ctl`. O Airflow armazena credenciais no metastore/secret backend; para produção habilite Fernet key e secret backend apropriado.
