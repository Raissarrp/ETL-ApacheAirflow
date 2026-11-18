def criar_datas(conexao_destino, registros):
    datas = sorted(set(registro[2] for registro in registros))

    linhas_datas = [
        (
            int(data.strftime("%Y%m%d")),
            data,
            data.year,
            (data.month - 1) // 3 + 1,
            data.month,
            data.strftime("%B"),
            data.day,
        )
        for data in datas
    ]

    with conexao_destino.cursor() as cursor:
        from psycopg2.extras import execute_values

        execute_values(
            cursor,
            """
            INSERT INTO dw.dim_date(
                date_key,
                full_date,
                year,
                quarter,
                month,
                month_name,
                day
            )
            VALUES %s
            ON CONFLICT(date_key) DO NOTHING
            """,
            linhas_datas,
        )
