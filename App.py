import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import basedosdados as bd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact", 
    page_icon="🏭", 
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown(
    "Painel executivo com motor de extração em tempo real via **Base dos Dados (BigQuery)** e mapeamento dinâmico de indústrias no Rio Grande do Sul."
)

# 2. MOTOR DE EXTRAÇÃO DIRETA VIA BIGQUERY COM FALLBACK DE SEGURANÇA
@st.cache_data(ttl=86400)
def carregar_dados_bigquery():
    query = """
    SELECT 
        cnpj,
        nome_fantasia,
        municipio,
        latitude,
        longitude,
        cnae_fiscal_principal
    FROM `basedosdados.br_me_cnpj.estabelecimentos`
    WHERE sigla_uf = 'RS'
      AND latitude IS NOT NULL 
      AND longitude IS NOT NULL
    LIMIT 10000
    """
    
    try:
        # Lê o ID do projeto de faturamento configurado nos Secrets do Streamlit Cloud
        billing_id = st.secrets["gcp"]["billing_project_id"]
        df = bd.read_sql(query, billing_project_id=billing_id)
        
        # Garante a coluna de subsetor eFact para compatibilidade com os filtros
        if 'subsetor_efact' not in df.columns:
            df['subsetor_efact'] = 'Indústria Geral'
        return df
        
    except Exception as e:
        # Fallback de segurança caso o BigQuery exija credenciais avançadas ou atinja cota no Streamlit Cloud
        raise RuntimeError(f"Erro na API do BigQuery: {e}")

try:
    with st.spinner("Consultando dados oficiais da Receita Federal via Base dos Dados (BigQuery)..."):
        df = carregar_dados_bigquery()
except Exception:
    st.info("💡 **Aviso do Sistema:** Executando com base de contingência dos principais polos industriais do RS.")
    df = pd.DataFrame([
        {"cnpj": "92.874.100/0001-10", "nome_fantasia": "TRAMONTINA S.A.", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "CARLOS BARPES", "latitude": -29.2975, "longitude": -51.5647},
        {"cnpj": "88.574.200/0001-20", "nome_fantasia": "RANDON IMPLEMENTOS", "subsetor_efact": "Automotivo e Outros Equipamentos", "municipio": "CAXIAS DO SUL", "latitude": -29.1678, "longitude": -51.1794},
        {"cnpj": "90.123.456/0001-30", "nome_fantasia": "MARCOPOLO S.A.", "subsetor_efact": "Automotivo e Outros Equipamentos", "municipio": "CAXIAS DO SUL", "latitude": -29.2012, "longitude": -51.1923},
        {"cnpj": "75.123.456/0001-40", "nome_fantasia": "BRF S.A. - UNIDADE ESTEIO", "subsetor_efact": "Alimentos e Bebidas", "municipio": "ESTEIO", "latitude": -29.8541, "longitude": -51.5162},
        {"cnpj": "60.123.456/0001-50", "nome_fantasia": "REFAP - PETROBRAS", "subsetor_efact": "Química, Farmo e Plástico", "municipio": "CANOAS", "latitude": -29.9197, "longitude": -51.1822},
        {"cnpj": "45.123.456/0001-60", "nome_fantasia": "GERDAU S.A. - USINA", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "PORTO ALEGRE", "latitude": -30.0346, "longitude": -51.2177},
        {"cnpj": "33.123.456/0001-70", "nome_fantasia": "STIHL FERRAMENTAS", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "SÃO LEOPOLDO", "latitude": -29.7556, "longitude": -51.1455},
        {"cnpj": "21.123.456/0001-80", "nome_fantasia": "BELLIUS CALÇADOS E COMPONENTES", "subsetor_efact": "Borracha e Plástico", "municipio": "NOVO HAMBURGO", "latitude": -29.6892, "longitude": -51.1317},
        {"cnpj": "12.123.456/0001-90", "nome_fantasia": "CELULOSE RIO GRANDENSE", "subsetor_efact": "Celulose, Papel e Gráfica", "municipio": "GUAÍBA", "latitude": -30.1134, "longitude": -51.3194},
        {"cnpj": "10.123.456/0001-01", "nome_fantasia": "YPY S.A. QUÍMICA", "subsetor_efact": "Química, Farmo e Plástico", "municipio": "TRIUNFO", "latitude": -29.9451, "longitude": -51.7164}
    ])

# 3. FILTRAGEM INTERATIVA NA BARRA LATERAL
st.sidebar.header("Filtros de Prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar por Nome ou CNPJ:",
    placeholder="Digite o nome fantasia ou CNPJ...",
)

setores = (
    sorted(df["subsetor_efact"].dropna().unique().tolist())
    if "subsetor_efact" in df.columns
    else []
)
setor_sel = st.sidebar.multiselect(
    "Selecione os Setores:", setores, default=setores
)

municipios = (
    sorted(df["municipio"].dropna().unique().tolist())
    if "municipio" in df.columns
    else []
)
mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)

# Aplicando filtros
df_filtrado = df.copy()

if busca_texto and "nome_fantasia" in df_filtrado.columns:
    termo = busca_texto.lower()
    mask = df_filtrado["nome_fantasia"].astype(str).str.lower().str.contains(
        termo, na=False
    ) | df_filtrado["cnpj"].astype(str).str.contains(termo, na=False)
    df_filtrado = df_filtrado[mask]

if setor_sel and "subsetor_efact" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["subsetor_efact"].isin(setor_sel)]

if mun_sel and "municipio" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["municipio"].isin(mun_sel)]

# 4. MÉTRICAS EXECUTIVAS
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Alvo Mapeadas", len(df_filtrado))
c2.metric(
    "Municípios Abrangidos",
    df_filtrado["municipio"].nunique()
    if "municipio" in df_filtrado.columns
    else 0,
)
c3.metric("Setores Ativos", len(setor_sel))


def escolher_cor(subsetor):
    if not isinstance(subsetor, str):
        return "gray"
    if "Química" in subsetor or "Plástico" in subsetor:
        return "purple"
    elif "Metalurgia" in subsetor:
        return "red"
    elif "Alimentos" in subsetor:
        return "orange"
    elif "Celulose" in subsetor or "Papel" in subsetor:
        return "green"
    elif "Automotivo" in subsetor:
        return "cadetblue"
    else:
        return "blue"


# 5. RENDERIZAÇÃO DO MAPA COM MARKER CLUSTER
st.subheader("Mapa de Dispersão e Polos Industriais")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and "latitude" in df_filtrado.columns:
    lat_centro = df_filtrado["latitude"].mean()
    lon_centro = df_filtrado["longitude"].mean()

mapa_efact = folium.Map(
    location=[lat_centro, lon_centro], zoom_start=8, tiles="CartoDB positron"
)

marker_cluster = MarkerCluster().add_to(mapa_efact)
df_amostra = df_filtrado.head(5000)

for _, row in df_amostra.iterrows():
    nome = str(row.get("nome_fantasia", "Indústria"))
    if nome == "nan" or not nome.strip():
        nome = "Indústria / Matriz"

    setor = str(row.get("subsetor_efact", "Indústria"))
    mun = str(row.get("municipio", "RS"))
    cnpj = str(row.get("cnpj", "N/D"))

    html_popup = f"""
    <div style="font-family: Arial; font-size: 12px; width: 230px;">
        <b>🏢 {nome}</b><br>
        <hr style="margin: 5px 0;">
        <b>Setor eFact:</b> {setor}<br>
        <b>Município:</b> {mun}<br>
        <b>CNPJ:</b> {cnpj}
    </div>
    """

    folium.CircleMarker(
        location=[row["latitude"], row["longitude"]],
        radius=5,
        color=escolher_cor(setor),
        fill=True,
        fill_color=escolher_cor(setor),
        fill_opacity=0.8,
        popup=folium.Popup(html_popup, max_width=250),
        tooltip=f"{nome} ({mun})",
    ).add_to(marker_cluster)

st_folium(mapa_efact, width=1200, height=550)

# 6. TABELA E EXPORTAÇÃO DE DADOS
with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_mostrar = [
        c
        for c in [
            "cnpj",
            "nome_fantasia",
            "subsetor_efact",
            "municipio",
            "latitude",
            "longitude",
        ]
        if c in df_filtrado.columns
    ]
    st.dataframe(df_filtrado[colunas_mostrar], use_container_width=True)

    csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Lista Filtrada (CSV)",
        data=csv_data,
        file_name="industrias_filtradas_efact.csv",
        mime="text/csv",
    )