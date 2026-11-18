"""DAG principal: somente orquestra as tarefas; a lógica fica em aw_etl/."""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from aw_etl.queries import DIMENSIONS
from aw_etl.incremental import load_dimension, validate_structures, verify_connections
from aw_etl.fact import load_fact
from aw_etl.quality import quality_checks

with DAG(
    "adventureworks_star_incremental",
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
    verify = PythonOperator(
        task_id="verify_connections",
        python_callable=verify_connections,
    )
    validate = PythonOperator(
        task_id="validate_structures",
        python_callable=validate_structures,
    )
    dims = [
        PythonOperator(
            task_id=f"load_dim_{name}",
            python_callable=load_dimension,
            op_kwargs={"name": name},
        )
        for name in DIMENSIONS
    ]
    fact = PythonOperator(task_id="load_fact_sales", python_callable=load_fact)
    checks = PythonOperator(task_id="quality_checks", python_callable=quality_checks)

    verify >> validate >> dims >> fact >> checks
