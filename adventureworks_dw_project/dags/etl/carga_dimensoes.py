from etl.configuracoes import DIMENSOES
from etl.controle_incremental import executar_carga_incremental


def carregar_dimensao(nome_dimensao):
    consulta, colunas, chave_negocio = DIMENSOES[nome_dimensao]
    executar_carga_incremental(
        nome_pipeline=nome_dimensao,
        consulta_origem=consulta,
        colunas=colunas,
        chave_negocio=chave_negocio,
    )
