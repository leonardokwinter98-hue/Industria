import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import basedosdados as bd
import json
import os

# 1. AUTENTICAÇÃO AUTOMÁTICA DA CONTA DE SERVIÇO VIA SECRETS
if "gcp" in st.secrets:
    creds_dict = dict(st.secrets["gcp"])
    creds_path = "/tmp/gcp_creds.json"
    with open(creds_path, "w") as f:
        json.dump(creds_dict, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

# 2. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact RS", 
    page_icon="🏭", 
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown(
    "Painel executivo com motor de extração em tempo real via **Base dos Dados (BigQuery)** — Abrangência Estadual (RS)."
)

# 3. EXTRAÇÃO REAL E DIRETA DO BIGQUERY
@st.cache_data(ttl=86400)
def carregar_dados_reais_bigquery():
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
      AND (SUBSTR(e.cnae_fiscal_principal, 1, 2) BETWEEN '10' AND '33' 
           OR SUBSTR(e.cnae_fiscal_principal, 1, 2) BETWEEN '05' AND '09')
    LIMIT 25000
    """
    
    gcp_sec = st.secrets.get("gcp", {})
    billing_id = gcp_sec.get("project_id", gcp_sec.get("billing_project_id", "tough-hologram-459312-e4"))
    
    df = bd.read_sql(query, billing_project_id=billing_id)
    
    mapeamento_porte = {
        '01': 'Não Aplicável',
        '03': 'Microempresa (ME)',
        '05': 'Empresa de Pequeno Porte (EPP)',
        '09': 'Demais (Média/Grande Porte)'
    }
    df['porte_descricao'] = df['porte'].astype(str).map(mapeamento_porte).fillna('Outros / Não Informado')
    
    def classificar_setor(cnae):
        cnae_str = str(cnae)
        if cnae_str.startswith(('10', '11', '12')): return 'Alimentos e Bebidas'
        elif cnae_str.startswith(('19', '20', '21', '22')): return 'Química, Farmo e Plástico'
        elif cnae_str.startswith(('24', '25')): return 'Metalurgia e Metalmecânica'
        elif cnae_str.startswith(('17', '18')): return 'Celulose, Papel e Gráfica'
        elif cnae_str.startswith(('29', '30')): return 'Automotivo e Outros Equipamentos'
        elif cnae_str.startswith(('13', '14', '15')): return 'Têxtil, Calçados e Couro'
        else: return 'Indústria de Transformação Geral'

    df['subsetor_efact'] = df['cnae_fiscal_principal'].apply(classificar_setor)
    return df

try:
    with st.spinner("Executando consulta oficial no BigQuery (Base dos Dados) para todo o RS..."):
        df = carregar_dados_reais_bigquery()
except Exception as e:
    st.error(f"❌ Erro ao conectar com o BigQuery: {e}")
    st.stop()

# 4. FILTRAGEM INTERATIVA NA BARRA LATERAL
st.sidebar.header("Filtros de Prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar por Nome ou CNPJ:",
    placeholder="Digite o nome fantasia ou CNPJ...",
)

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

# 5. MÉTRICAS EXECUTIVAS
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Mapeadas (RS)", len(df_filtrado))
c2.metric(
    "Municípios Cobertos",
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
    elif "Têxtil" in subsetor:
        return "pink"
    else:
        return "blue"

# 6. RENDERIZAÇÃO DO MAPA
st.subheader("Mapa de Dispersão Industrial - Rio Grande do Sul")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and "latitude" in df_filtrado.columns:
    lat_centro = df_filtrado["latitude"].mean()
    lon_centro = df_filtrado["longitude"].mean()

mapa_efact = folium.Map(
    location=[-30.2, -53.5], zoom_start=7, tiles="CartoDB positron"
)

marker_cluster = MarkerCluster().add_to(mapa_efact)
df_amostra = df_filtrado.head(8000)

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

st_folium(mapa_efact, width=1200, height=600)

# 7. TABELA E EXPORTAÇÃO
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
        file_name="industrias_rs_real_efact.csv",
        mime="text/csv",
    )