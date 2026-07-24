"""
eFact — Painel de Geomarketing Industrial

Este app NÃO consulta o BigQuery diretamente.
Ele lê o arquivo industrias_rs_efact.parquet gerado pelo Colab.

Fluxo:
    Colab gera o Parquet -> Streamlit lê o Parquet -> usuário filtra e visualiza
"""

from html import escape
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


# =============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA
# =============================================================================
# Este comando deve aparecer apenas uma vez e antes dos demais comandos
# visuais do Streamlit.

st.set_page_config(
    page_title="Geomarketing Industrial | eFact RS",
    page_icon="🏭",
    layout="wide",
)


# =============================================================================
# 2. CONFIGURAÇÕES DO APLICATIVO
# =============================================================================

# Os dois Colabs devem salvar o resultado final com este mesmo nome.
ARQUIVO_PARQUET = Path("industrias_rs_efact.parquet")

# Mostrar pontos demais deixa o mapa lento no navegador.
# Este limite vale apenas para o mapa. A tabela e o CSV mantêm todos os dados.
LIMITE_PONTOS_MAPA = 5_000


# =============================================================================
# 3. FUNÇÕES DE APOIO
# =============================================================================


def classificar_grupo_industrial(cnae):
    """Cria o grupo industrial quando a coluna não vier pronta no Parquet."""

    cnae = str(cnae).strip()

    # Alguns arquivos podem trazer o CNAE como 1011201.0.
    if cnae.endswith(".0"):
        cnae = cnae[:-2]

    cnae = cnae.zfill(7)

    if not cnae[:2].isdigit():
        return "Não classificado"

    divisao = int(cnae[:2])

    if 5 <= divisao <= 9:
        return "Indústrias extrativas"
    if 10 <= divisao <= 32:
        return "Indústrias de transformação"
    if divisao == 33:
        return "Manutenção, reparação e instalação industrial"

    return "Outros"


def classificar_subsetor(cnae):
    """Cria uma classificação comercial simplificada a partir do CNAE."""

    cnae = str(cnae).strip()

    if cnae.endswith(".0"):
        cnae = cnae[:-2]

    cnae = cnae.zfill(7)

    if not cnae[:2].isdigit():
        return "Não classificado"

    divisao = int(cnae[:2])

    if 5 <= divisao <= 9:
        return "Indústrias extrativas"
    if 10 <= divisao <= 12:
        return "Alimentos, bebidas e fumo"
    if 13 <= divisao <= 15:
        return "Têxtil, vestuário, couro e calçados"
    if divisao == 16:
        return "Madeira"
    if 17 <= divisao <= 18:
        return "Celulose, papel e gráfica"
    if 19 <= divisao <= 23:
        return "Química, farmacêutica, plástico e minerais"
    if 24 <= divisao <= 25:
        return "Metalurgia e produtos de metal"
    if 26 <= divisao <= 28:
        return "Eletrônicos, máquinas e equipamentos"
    if 29 <= divisao <= 30:
        return "Automotivo e equipamentos de transporte"
    if 31 <= divisao <= 32:
        return "Móveis e outras manufaturas"
    if divisao == 33:
        return "Manutenção e instalação industrial"

    return "Não classificado"


def escolher_cor(subsetor):
    """Define a cor dos pontos no mapa de acordo com o subsetor."""

    if pd.isna(subsetor):
        return "gray"

    subsetor = str(subsetor)

    if "Química" in subsetor or "Plástico" in subsetor:
        return "purple"
    if "Metalurgia" in subsetor:
        return "red"
    if "Alimentos" in subsetor:
        return "orange"
    if "Celulose" in subsetor or "Papel" in subsetor:
        return "green"
    if "Automotivo" in subsetor:
        return "cadetblue"
    if "Têxtil" in subsetor:
        return "pink"
    if "Madeira" in subsetor or "Móveis" in subsetor:
        return "darkgreen"
    if "Manutenção" in subsetor:
        return "darkblue"
    if "Extrativas" in subsetor:
        return "black"

    return "blue"


def texto_popup(valor, padrao="Não informado"):
    """Converte um valor para texto seguro antes de colocá-lo no HTML."""

    if pd.isna(valor):
        return escape(padrao)

    texto = str(valor).strip()

    if texto == "" or texto.lower() == "nan":
        texto = padrao

    return escape(texto)


def formatar_capital_social(valor):
    """Formata o capital social apenas para exibição no popup."""

    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor):
        return "Não informado"

    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


# =============================================================================
# 4. CARREGAMENTO E PREPARAÇÃO DOS DADOS
# =============================================================================


@st.cache_data
# O cache evita reler o Parquet toda vez que o usuário altera um filtro.
def carregar_dados():
    """Lê o Parquet e deixa as colunas prontas para o painel."""

    df = pd.read_parquet(ARQUIVO_PARQUET)

    # Estas colunas são necessárias para o funcionamento básico do app.
    colunas_obrigatorias = {
        "cnpj",
        "municipio",
        "latitude",
        "longitude",
        "cnae_fiscal_principal",
    }

    colunas_ausentes = colunas_obrigatorias - set(df.columns)

    if colunas_ausentes:
        raise ValueError(
            "Colunas obrigatórias ausentes no Parquet: "
            + ", ".join(sorted(colunas_ausentes))
        )

    # Cria campos opcionais quando eles não existirem.
    # Isso permite que o app leia tanto o Parquet simples quanto o avançado.
    colunas_opcionais = [
        "nome_fantasia",
        "razao_social",
        "cep",
        "logradouro",
        "numero",
        "porte",
        "porte_descricao",
        "grupo_industrial",
        "subsetor_efact",
        "capital_social",
    ]

    for coluna in colunas_opcionais:
        if coluna not in df.columns:
            df[coluna] = pd.NA

    # Coordenadas inválidas são transformadas em valores vazios.
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["capital_social"] = pd.to_numeric(df["capital_social"], errors="coerce")

    # CNPJ, CEP e CNAE são identificadores. Devem permanecer como texto.
    df["cnpj"] = df["cnpj"].astype("string").str.replace(r"\.0$", "", regex=True)
    df["cep"] = df["cep"].astype("string").str.replace(r"\.0$", "", regex=True)
    df["cnae_fiscal_principal"] = (
        df["cnae_fiscal_principal"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(7)
    )

    # Fallback do porte: usado somente quando porte_descricao não veio pronto.
    mapeamento_porte = {
        "00": "Não informado",
        "01": "Microempresa",
        "03": "Empresa de Pequeno Porte",
        "05": "Demais empresas",
    }

    porte_codigo = (
        df["porte"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )

    porte_calculado = porte_codigo.map(mapeamento_porte).fillna(
        "Código não identificado"
    )

    df["porte_descricao"] = (
        df["porte_descricao"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(porte_calculado)
    )

    # Os dois Colabs atuais já geram estas colunas.
    # O cálculo abaixo é apenas uma proteção para versões anteriores.
    grupo_calculado = df["cnae_fiscal_principal"].apply(
        classificar_grupo_industrial
    )

    df["grupo_industrial"] = (
        df["grupo_industrial"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(grupo_calculado)
    )

    subsetor_calculado = df["cnae_fiscal_principal"].apply(classificar_subsetor)

    df["subsetor_efact"] = (
        df["subsetor_efact"]
        .astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna(subsetor_calculado)
    )

    # Nome principal usado no mapa.
    nome_fantasia = (
        df["nome_fantasia"].astype("string").str.strip().replace("", pd.NA)
    )
    razao_social = (
        df["razao_social"].astype("string").str.strip().replace("", pd.NA)
    )

    df["nome_empresa"] = nome_fantasia.fillna(razao_social).fillna(
        "Empresa sem nome informado"
    )

    # Marca quais registros realmente podem ser desenhados no mapa.
    df["possui_coordenada"] = (
        df["latitude"].between(-90, 90)
        & df["longitude"].between(-180, 180)
    )

    # Remove possíveis duplicidades acidentais do mesmo CNPJ.
    # Quando houver duas linhas, damos preferência à que tem coordenadas.
    df = (
        df.sort_values(
            ["cnpj", "possui_coordenada"],
            ascending=[True, False],
        )
        .drop_duplicates(subset=["cnpj"], keep="first")
        .reset_index(drop=True)
    )

    return df


# O app para com uma mensagem compreensível quando o arquivo não existe.
if not ARQUIVO_PARQUET.exists():
    st.error(f"Arquivo não encontrado: {ARQUIVO_PARQUET.name}")
    st.info(
        "Gere o Parquet no Colab e coloque-o na mesma pasta do app.py. "
        "O nome esperado é industrias_rs_efact.parquet."
    )
    st.stop()

try:
    with st.spinner("Carregando a base industrial..."):
        df = carregar_dados()
except Exception as erro:
    st.error("Não foi possível carregar o arquivo Parquet.")
    st.exception(erro)
    st.stop()


# =============================================================================
# 5. CABEÇALHO
# =============================================================================

st.title("🎯 eFact — Inteligência de Expansão Comercial e Geomarketing")
st.markdown(
    "Painel para explorar potenciais operações industriais no Rio Grande do Sul."
)

# Mostra a data da fotografia cadastral, quando existir no arquivo.
if "data_referencia" in df.columns:
    data_referencia = pd.to_datetime(df["data_referencia"], errors="coerce").max()

    if pd.notna(data_referencia):
        st.caption(
            f"Base cadastral de referência: {data_referencia:%d/%m/%Y}. "
            "As coordenadas representam o centro aproximado do CEP."
        )
else:
    st.caption("As coordenadas representam o centro aproximado do CEP.")


# =============================================================================
# 6. FILTROS DA BARRA LATERAL
# =============================================================================

st.sidebar.header("Filtros de prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar empresa ou CNPJ",
    placeholder="Nome fantasia, razão social ou CNPJ...",
)

# Primeiro filtro: grupo amplo de atividade.
grupos_disponiveis = sorted(
    df["grupo_industrial"].dropna().astype(str).unique().tolist()
)

# O painel inicia priorizando indústrias de transformação.
grupo_padrao = (
    ["Indústrias de transformação"]
    if "Indústrias de transformação" in grupos_disponiveis
    else grupos_disponiveis
)

grupo_sel = st.sidebar.multiselect(
    "Grupo industrial",
    options=grupos_disponiveis,
    default=grupo_padrao,
)

portes_disponiveis = sorted(
    df["porte_descricao"].dropna().astype(str).unique().tolist()
)
porte_sel = st.sidebar.multiselect(
    "Porte cadastral",
    options=portes_disponiveis,
    default=portes_disponiveis,
)

setores_disponiveis = sorted(
    df["subsetor_efact"].dropna().astype(str).unique().tolist()
)
setor_sel = st.sidebar.multiselect(
    "Subsetor",
    options=setores_disponiveis,
    default=setores_disponiveis,
)

municipios_disponiveis = sorted(
    df["municipio"].dropna().astype(str).unique().tolist()
)
municipio_sel = st.sidebar.multiselect(
    "Município",
    options=municipios_disponiveis,
)


# =============================================================================
# 7. APLICAÇÃO DOS FILTROS
# =============================================================================

# copy() evita alterar o DataFrame original armazenado em cache.
df_filtrado = df.copy()

if busca_texto.strip():
    termo = busca_texto.strip()

    # regex=False trata a pesquisa como texto comum.
    mascara_busca = (
        df_filtrado["nome_fantasia"]
        .fillna("")
        .astype(str)
        .str.contains(termo, case=False, regex=False)
        | df_filtrado["razao_social"]
        .fillna("")
        .astype(str)
        .str.contains(termo, case=False, regex=False)
        | df_filtrado["cnpj"]
        .fillna("")
        .astype(str)
        .str.contains(termo, case=False, regex=False)
    )

    df_filtrado = df_filtrado[mascara_busca]

if grupo_sel:
    df_filtrado = df_filtrado[
        df_filtrado["grupo_industrial"].isin(grupo_sel)
    ]

if porte_sel:
    df_filtrado = df_filtrado[
        df_filtrado["porte_descricao"].isin(porte_sel)
    ]

if setor_sel:
    df_filtrado = df_filtrado[
        df_filtrado["subsetor_efact"].isin(setor_sel)
    ]

if municipio_sel:
    df_filtrado = df_filtrado[
        df_filtrado["municipio"].isin(municipio_sel)
    ]

# Importante:
# empresas sem coordenadas continuam na tabela e no arquivo CSV.
# Apenas o DataFrame abaixo é limitado aos registros que podem ir ao mapa.
df_mapa = df_filtrado[df_filtrado["possui_coordenada"]].copy()


# =============================================================================
# 8. MÉTRICAS
# =============================================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric("Empresas filtradas", f"{len(df_filtrado):,}".replace(",", "."))
c2.metric("Empresas no mapa", f"{len(df_mapa):,}".replace(",", "."))
c3.metric(
    "Municípios",
    df_filtrado["municipio"].nunique() if not df_filtrado.empty else 0,
)
c4.metric(
    "Subsetores",
    df_filtrado["subsetor_efact"].nunique() if not df_filtrado.empty else 0,
)


# =============================================================================
# 9. MAPA
# =============================================================================

st.subheader("Mapa de dispersão industrial — Rio Grande do Sul")

if df_mapa.empty:
    st.warning("Nenhuma empresa com coordenadas atende aos filtros selecionados.")
else:
    # A mediana reduz o efeito de alguma coordenada muito afastada.
    latitude_centro = float(df_mapa["latitude"].median())
    longitude_centro = float(df_mapa["longitude"].median())

    mapa_efact = folium.Map(
        location=[latitude_centro, longitude_centro],
        zoom_start=7,
        tiles="CartoDB positron",
    )

    agrupador = MarkerCluster().add_to(mapa_efact)

    # O mapa recebe somente os primeiros pontos até o limite configurado.
    # A tabela e o download continuam contendo todas as empresas filtradas.
    df_pontos = df_mapa.head(LIMITE_PONTOS_MAPA)

    if len(df_mapa) > LIMITE_PONTOS_MAPA:
        st.info(
            f"O mapa apresenta {LIMITE_PONTOS_MAPA:,} de "
            f"{len(df_mapa):,} empresas geocodificadas. "
            "A tabela e o CSV contêm todos os resultados filtrados."
        )

    for _, empresa in df_pontos.iterrows():
        nome = texto_popup(empresa.get("nome_empresa"), "Empresa")
        nome_fantasia = texto_popup(empresa.get("nome_fantasia"))
        razao_social = texto_popup(empresa.get("razao_social"))
        municipio = texto_popup(empresa.get("municipio"), "RS")
        cnpj = texto_popup(empresa.get("cnpj"))
        porte = texto_popup(empresa.get("porte_descricao"))
        grupo = texto_popup(empresa.get("grupo_industrial"))
        subsetor = texto_popup(empresa.get("subsetor_efact"))
        cnae = texto_popup(empresa.get("cnae_fiscal_principal"))
        logradouro = texto_popup(empresa.get("logradouro"), "")
        numero = texto_popup(empresa.get("numero"), "")
        capital = escape(formatar_capital_social(empresa.get("capital_social")))

        endereco = f"{logradouro}, {numero}".strip(" ,")
        if endereco == "":
            endereco = "Não informado"

        popup = f"""
        <div style="font-family: Arial; font-size: 12px; width: 285px;">
            <b>🏢 {nome}</b><br>
            <hr style="margin: 6px 0;">
            <b>Nome fantasia:</b> {nome_fantasia}<br>
            <b>Razão social:</b> {razao_social}<br>
            <b>Endereço:</b> {endereco}<br>
            <b>Município:</b> {municipio}<br>
            <b>Grupo:</b> {grupo}<br>
            <b>Subsetor:</b> {subsetor}<br>
            <b>CNAE:</b> {cnae}<br>
            <b>Porte cadastral:</b> {porte}<br>
            <b>Capital social:</b> {capital}<br>
            <b>CNPJ:</b> {cnpj}<br>
            <hr style="margin: 6px 0;">
            <small>Localização aproximada pelo centroide do CEP.</small>
        </div>
        """

        cor = escolher_cor(empresa.get("subsetor_efact"))

        folium.CircleMarker(
            location=[empresa["latitude"], empresa["longitude"]],
            radius=4,
            color=cor,
            fill=True,
            fill_color=cor,
            fill_opacity=0.8,
            popup=folium.Popup(popup, max_width=320),
            tooltip=f"{nome} ({municipio})",
        ).add_to(agrupador)

    st_folium(
        mapa_efact,
        use_container_width=True,
        height=600,
        returned_objects=[],
    )


# =============================================================================
# 10. TABELA E DOWNLOAD
# =============================================================================

texto_expander = f"Ver base detalhada ({len(df_filtrado):,} registros)"
texto_expander = texto_expander.replace(",", ".")

with st.expander(texto_expander):
    colunas_preferidas = [
        "cnpj",
        "nome_fantasia",
        "razao_social",
        "porte_descricao",
        "grupo_industrial",
        "subsetor_efact",
        "cnae_fiscal_principal",
        "municipio",
        "logradouro",
        "numero",
        "cep",
        "capital_social",
        "latitude",
        "longitude",
    ]

    # A lista abaixo evita erro caso alguma coluna opcional não exista.
    colunas_tabela = [
        coluna for coluna in colunas_preferidas if coluna in df_filtrado.columns
    ]

    tabela = df_filtrado[colunas_tabela].copy()

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
    )

    # O separador ponto e vírgula e o UTF-8-SIG facilitam a abertura no Excel
    # configurado em português e preservam corretamente os acentos.
    csv_data = df_filtrado.to_csv(
        index=False,
        sep=";",
    ).encode("utf-8-sig")

    st.download_button(
        label="📥 Baixar lista filtrada em CSV",
        data=csv_data,
        file_name="industrias_rs_efact_filtradas.csv",
        mime="text/csv",
    )
