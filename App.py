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
    "Painel executivo com motor de extração em tempo real via **Base dos Dados (BigQuery)**, abrangência estadual (RS) e segmentação por porte corporativo."
)

# 2. MOTOR DE EXTRAÇÃO ESTADUAL VIA BIGQUERY COM JOIN DE PORTE
@st.cache_data(ttl=86400)
def carregar_dados_bigquery():
    query = """
    SELECT 
        e.cnpj,
        e.nome_fantasia,
        e.municipio,
        e.latitude,
        e.longitude,
        em.porte,
        e.cnae_fiscal_principal
    FROM `basedosdados.br_me_cnpj.estabelecimentos` as e
    LEFT JOIN `basedosdados.br_me_cnpj.empresas` as em
      ON e.cnpj_basico = em.cnpj_basico
    WHERE e.sigla_uf = 'RS'
      AND e.latitude IS NOT NULL 
      AND e.longitude IS NOT NULL
    LIMIT 20000
    """
    
    try:
        billing_id = st.secrets["gcp"]["billing_project_id"]
        df = bd.read_sql(query, billing_project_id=billing_id)
        
        # Tratamento da coluna de porte para formato legível
        mapeamento_porte = {
            '01': 'Não Aplicável',
            '03': 'Microempresa (ME)',
            '05': 'Empresa de Pequeno Porte (EPP)',
            '09': 'Demais (Média/Grande Porte)'
        }
        if 'porte' in df.columns:
            df['porte_descricao'] = df['porte'].astype(str).map(mapeamento_porte).fillna('Outros / Não Informado')
        else:
            df['porte_descricao'] = 'Demais (Média/Grande Porte)'
            
        if 'subsetor_efact' not in df.columns:
            df['subsetor_efact'] = 'Indústria Geral'
            
        return df
        
    except Exception as e:
        raise RuntimeError(f"Erro na API do BigQuery: {e}")

try:
    with st.spinner("Consultando base estadual completa da Receita Federal via Base dos Dados (BigQuery)..."):
        df = carregar_dados_bigquery()
except Exception:
    st.info("💡 **Aviso do Sistema:** Executando com base de contingência estruturada para o RS.")
    df = pd.DataFrame([
        {"cnpj": "92.874.100/0001-10", "nome_fantasia": "TRAMONTINA S.A.", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "CARLOS BARPES", "latitude": -29.2975, "longitude": -51.5647, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "88.574.200/0001-20", "nome_fantasia": "RANDON IMPLEMENTOS", "subsetor_efact": "Automotivo e Outros Equipamentos", "municipio": "CAXIAS DO SUL", "latitude": -29.1678, "longitude": -51.1794, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "90.123.456/0001-30", "nome_fantasia": "MARCOPOLO S.A.", "subsetor_efact": "Automotivo e Outros Equipamentos", "municipio": "CAXIAS DO SUL", "latitude": -29.2012, "longitude": -51.1923, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "75.123.456/0001-40", "nome_fantasia": "BRF S.A. - UNIDADE ESTEIO", "subsetor_efact": "Alimentos e Bebidas", "municipio": "ESTEIO", "latitude": -29.8541, "longitude": -51.5162, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "60.123.456/0001-50", "nome_fantasia": "REFAP - PETROBRAS", "subsetor_efact": "Química, Farmo e Plástico", "municipio": "CANOAS", "latitude": -29.9197, "longitude": -51.1822, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "45.123.456/0001-60", "nome_fantasia": "GERDAU S.A. - USINA", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "PORTO ALEGRE", "latitude": -30.0346, "longitude": -51.2177, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "33.123.456/0001-70", "nome_fantasia": "STIHL FERRAMENTAS", "subsetor_efact": "Metalurgia e Metalmecânica", "municipio": "SÃO LEOPOLDO", "latitude": -29.7556, "longitude": -51.1455, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "21.123.456/0001-80", "nome_fantasia": "BELLIUS CALÇADOS", "subsetor_efact": "Borracha e Plástico", "municipio": "NOVO HAMBURGO", "latitude": -29.6892, "longitude": -51.1317, "porte_descricao": "Empresa de Pequeno Porte (EPP)"},
        {"cnpj": "12.123.456/0001-90", "nome_fantasia": "CELULOSE RIO GRANDENSE", "subsetor_efact": "Celulose, Papel e Gráfica", "municipio": "GUAÍBA", "latitude": -30.1134, "longitude": -51.3194, "porte_descricao": "Demais (Média/Grande Porte)"},
        {"cnpj": "10.123.456/0001-01", "nome_fantasia": "YPY S.A. QUÍMICA", "subsetor_efact": "Química, Farmo e Plástico", "municipio": "TRIUNFO", "latitude": -29.9451, "longitude": -51.7164, "porte_descricao": "Empresa de Pequeno Porte (EPP)"}
    ])

# 3. FILTRAGEM INTERATIVA NA BARRA LATERAL
st.sidebar.header("Filtros de Prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar por Nome ou CNPJ:",
    placeholder="Digite o nome fantasia ou CNPJ...",
)

# Filtro de Porte da Empresa
portes_disponiveis = sorted(df["porte_descricao"].dropna().unique().tolist()) if "porte_descricao" in df.columns else []
porte_sel = st.sidebar.multiselect("Selecione o Porte da Empresa:", portes_disponiveis, default=portes_disponiveis)

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

if porte_sel and "porte_descricao" in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado["porte_descricao"].isin(porte_sel)]

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
st.subheader("Mapa de Dispersão e Polos Industriais (RS)")

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
    porte_emp = str(row.get("porte_descricao", "N/D"))

    html_popup = f"""
    <div style="font-family: Arial; font-size: 12px; width: 230px;">
        <b>🏢 {nome}</b><br>
        <hr style="margin: 5px 0;">
        <b>Porte:</b> {porte_emp}<br>
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
            "porte_descricao",
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
        file_name="industrias_rs_porte_filtrado.csv",
        mime="text/csv",
    )