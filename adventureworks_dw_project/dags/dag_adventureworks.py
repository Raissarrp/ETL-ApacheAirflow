from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from etl.configuracoes import DIMENSOES
from etl.conexoes import verificar_conexoes, validar_estruturas
from etl.carga_dimensoes import carregar_dimensao
from etl.carga_vendas import carregar_vendas
from etl.validacao import verificar_qualidade


with DAG(
    dag_id="adventureworks_star_incremental",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    max_active_runs=1,
    default_args={
        "owner": "student",
        "retries": 2,
        "retry_delay": timedelta(minutes=3),
    },
    tags=["adventureworks", "etl", "star-schema"],
) as dag:
    tarefa_verificar_conexoes = PythonOperator(
        task_id="verify_connections",
        python_callable=verificar_conexoes,
    )
    tarefa_validar_estruturas = PythonOperator(
        task_id="validate_structures",
        python_callable=validar_estruturas,
    )

    tarefas_carregar_dimensoes = [
        PythonOperator(
            task_id=f"load_dim_{nome}",
            python_callable=carregar_dimensao,
            op_kwargs={"nome_dimensao": nome},
        )
        for nome in DIMENSOES
    ]

    tarefa_carregar_vendas = PythonOperator(
        task_id="load_fact_sales",
        python_callable=carregar_vendas,
    )
    tarefa_verificar_qualidade = PythonOperator(
        task_id="quality_checks",
        python_callable=verificar_qualidade,
    )

    (
        tarefa_verificar_conexoes
        >> tarefa_validar_estruturas
        >> tarefas_carregar_dimensoes
        >> tarefa_carregar_vendas
        >> tarefa_verificar_qualidade
    )
