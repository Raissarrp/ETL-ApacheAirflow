FROM apache/airflow:3.1.8

USER airflow
RUN pip install --no-cache-dir \
    apache-airflow-providers-microsoft-mssql \
    apache-airflow-providers-postgres \
    pymssql
