import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from google.cloud import bigquery
from google.oauth2 import service_account
import json
import os

# ====================== CREDENCIAIS GCP EMBUTIDAS (DIRETO NO CÓDIGO) ======================
creds_dict = {
  "type": "service_account",
  "project_id": "tough-hologram-459312-e4",
  "private_key_id": "74968bf4e443cab0722268d025c2bf810ad79b6e",
  "private_key": """-----BEGIN PRIVATE KEY-----
MIIEuwIBADANBgkqhkiG9w0BAQEFAASCBKUwggShAgEAAoIBAQC/ks9xC+xVurWo
Uc0TH2gdcYfczzM0Ef0ptZ0HdR7/kSjZHPRaPIFAXWwd5P5YMyy89tuzBO7eZ8Ss
VD+n6wBx2FJsfzAuLUiSJs6JBq0xMXvhPATqHpbFqQajcM+MRVw3DhbZESjyJmF1
gL17Ec+SaAaliCCAtlll4zPnU3zXyXN90Y6pooQD29CF9LrBfYzoCaHGmSffgN/b
F9GcPyQoi3TBm+qMs418p7BAyg3Tc5G+FNN8N3qrEya5X5fWw5tBcX7re2NXenOC
QfgEplFdkhBn0V877UZJK+TZjgWNUbzR/LTWFNrmkicF4Ay4c69Un4QftrcrTUTN
rD2DU/ztAgMBAAECgf8PCDcs2ROA8vQ3rLpCVZdclCkv9HmE21THv6najaJ+Plpz
8jj7YmW0ftGMuF3DknZOineTWiCVmuQyI7+OmnHD0nR4VtfqQO+9Mseavo0OYRcC
CjXawcYXYqC7bM3X3ovyDdgf7ONyCtROjHq0kEnqwsWe0DyUP8O2kE7TKNTdXQi8
Qb5UXIYp7fOXAKL+VbGyWHR6VnsmUtfUdOEMZN5GN8GJytsLE3/AsiWvw2gH5UMk
Rmb88xR0rwt5suq+fLNYShid8fXXVqBhk1u7qdfM5R3dF0QOUxTCkUSdonws+N8q
KIhPF94w0ggtaHOeYekxO3IseJRBNxzCoMdMdiECgYEA+D5Lb3t4PTuJm7I6g7k/
nL88jfCIl0uXLCw9Ck/DfFp6lhujqWLVG9GcdDfAtZ9uYSIYNWd35mqf/8bgQlkY
WigQ8TAjV0l48P22yctz/OoeDiVcpJHRxUx9hYuakyDoNlC+Fn8EDsFluR6scZip
DAsp0re02fsvlDcDJgLesgkCgYEAxY82PNKAbpgPc4S3/6KnM4EOqotYokm20UBj
S0KExC3HmKV27IIoeBjMHlf7o7bEo/MLJgTcrCbX3gs6KoHo4qdBOJ9RIx+puCyP
ZRdhxCS9DyxcDNwLOXs8NkpFjsaAZa7rSB6TIGTXUGsYzxoUme/fThsJCdJfcIJE
/g2cHMUCgYAEhc4GB+/W3cDSD1s1jyhziKBnzZwPdZcZfOzXxUBAgb1+Ap7mtSBA
037QNzvRk0gFiQN75Zivn/2uQUdQriLdcaFtY30hV/tWGKk93/ELCJDnnRKlBOsX
dx9KUZLNX2obozjzW/kM88UQrFhj8W4TBCg1aJdo6USipKXwCVlZUQKBgCHuTupz
XQuhokW87b1COmVmLRatiDOXZYbbADLU4eiv1DArexlz4W9/Es/DXLzpjyx5edi1
zRDkOv8v/nV+inkjMNiAxHa74XJ4dMhwE6KUjMQmYkjzIhplSBoq93dmMHdGa7Kf
TbWqnDB7tG8dk5w8zqWjjxHYx/uS5DaeL8nhAoGBAKghInB2EO4L7cI8b5wstbKo
IQ3HVWwN027dUtg7wjeXUzuBS5J5rtNGjnsC030JtiZ31mxa+FV7ToS8DL9EfykH
vBI3OqGh3kxGATmMllDvy5PjtqMMDMjzT8L24LQHj8dPy8FNxrvBagrStqoADlnl/
RkqBUkmiJ5jNTTqyr2c
-----END PRIVATE KEY-----""",
  "client_email": "leokw-487@tough-hologram-459312-e4.iam.gserviceaccount.com",
  "client_id": "103802563217312874235",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/leokw-487%40tough-hologram-459312-e4.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

# Inicializa o arquivo temporário de credenciais para a API do Google Cloud
creds_path = "/tmp/gcp_creds.json"
with open(creds_path, "w", encoding="utf-8") as f:
    json.dump(creds_dict, f, ensure_ascii=False, indent=2)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_path

# ====================== CONFIGURAÇÃO DA PÁGINA ======================
st.set_page_config(
    page_title="Geomarketing Industrial | eFact RS", 
    page_icon="🏭", 
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Painel executivo com motor de extração em tempo real via **BigQuery** — Abrangência Estadual (RS).")

# ====================== CARREGAMENTO DE DADOS ======================
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
    
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    client = bigquery.Client(
        project=creds_dict.get("project_id"), 
        credentials=credentials
    )
    
    df = client.query(query).to_dataframe()
    
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
    with st.spinner("Executando consulta oficial no BigQuery para todo o RS..."):
        df = carregar_dados_reais_bigquery()
except Exception as e:
    st.error(f"❌ Erro ao conectar com o BigQuery: {e}")
    st.stop()

# ====================== FILTROS LATERAIS ======================
st.sidebar.header("Filtros de Prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar por Nome ou CNPJ:", 
    placeholder="Digite o nome fantasia ou CNPJ..."
)

portes_disponiveis = sorted(df["porte_descricao"].dropna().unique().tolist()) if "porte_descricao" in df.columns else []
porte_sel = st.sidebar.multiselect("Selecione o Porte da Empresa:", portes_disponiveis, default=portes_disponiveis)

setores = sorted(df["subsetor_efact"].dropna().unique().tolist()) if "subsetor_efact" in df.columns else []
setor_sel = st.sidebar.multiselect("Selecione os Setores:", setores, default=setores)

municipios = sorted(df["municipio"].dropna().unique().tolist()) if "municipio" in df.columns else []
mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)

# Aplicação dos filtros
df_filtrado = df.copy()

if busca_texto:
    termo = busca_texto.lower()
    mask = (
        df_filtrado["nome_fantasia"].astype(str).str.lower().str.contains(termo, na=False) |
        df_filtrado["cnpj"].astype(str).str.contains(termo, na=False)
    )
    df_filtrado = df_filtrado[mask]

if porte_sel:
    df_filtrado = df_filtrado[df_filtrado["porte_descricao"].isin(porte_sel)]
if setor_sel:
    df_filtrado = df_filtrado[df_filtrado["subsetor_efact"].isin(setor_sel)]
if mun_sel:
    df_filtrado = df_filtrado[df_filtrado["municipio"].isin(mun_sel)]

# ====================== MÉTRICAS ======================
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Mapeadas (RS)", len(df_filtrado))
c2.metric("Municípios Cobertos", df_filtrado["municipio"].nunique() if not df_filtrado.empty else 0)
c3.metric("Setores Ativos", len(setor_sel))

# ====================== MAPA ======================
def escolher_cor(subsetor):
    if not isinstance(subsetor, str):
        return "gray"
    if "Química" in subsetor or "Plástico" in subsetor: return "purple"
    elif "Metalurgia" in subsetor: return "red"
    elif "Alimentos" in subsetor: return "orange"
    elif "Celulose" in subsetor or "Papel" in subsetor: return "green"
    elif "Automotivo" in subsetor: return "cadetblue"
    elif "Têxtil" in subsetor: return "pink"
    else: return "blue"

st.subheader("Mapa de Dispersão Industrial - Rio Grande do Sul")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty:
    lat_centro = df_filtrado["latitude"].mean()
    lon_centro = df_filtrado["longitude"].mean()

mapa_efact = folium.Map(location=[-30.2, -53.5], zoom_start=7, tiles="CartoDB positron")
marker_cluster = MarkerCluster().add_to(mapa_efact)

df_amostra = df_filtrado.head(8000)

for _, row in df_amostra.iterrows():
    nome = str(row.get("nome_fantasia", "Indústria")).strip()
    if nome in ["nan", ""]: 
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

# ====================== TABELA E DOWNLOAD ======================
with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_mostrar = [c for c in ["cnpj", "nome_fantasia", "porte_descricao", 
                                   "subsetor_efact", "municipio", "latitude", "longitude"] 
                       if c in df_filtrado.columns]
    
    st.dataframe(df_filtrado[colunas_mostrar], use_container_width=True)
    
    csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Lista Filtrada (CSV)",
        data=csv_data,
        file_name="industrias_rs_real_efact.csv",
        mime="text/csv",
    )

# ====================== CONFIGURAÇÃO DA PÁGINA ======================
st.set_page_config(
    page_title="Geomarketing Industrial | eFact RS",
    page_icon="🏭",
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Painel executivo com motor de extração em tempo real via **BigQuery** — Abrangência Estadual (RS).")

# ====================== AUTENTICAÇÃO ======================
try:
    creds_dict = setup_gcp_credentials()
except Exception as e:
    st.error(f"Erro na configuração das credenciais: {e}")
    st.stop()

# ====================== CARREGAMENTO DE DADOS ======================
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
    
    # Usa credenciais diretamente (mais confiável)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    client = bigquery.Client(
        project=creds_dict.get("project_id"), 
        credentials=credentials
    )
    
    df = client.query(query).to_dataframe()
    
    # Mapeamento de porte
    mapeamento_porte = {
        '01': 'Não Aplicável',
        '03': 'Microempresa (ME)',
        '05': 'Empresa de Pequeno Porte (EPP)',
        '09': 'Demais (Média/Grande Porte)'
    }
    df['porte_descricao'] = df['porte'].astype(str).map(mapeamento_porte).fillna('Outros / Não Informado')
    
    # Classificação de subsetor
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
    with st.spinner("Executando consulta oficial no BigQuery para todo o RS..."):
        df = carregar_dados_reais_bigquery()
except Exception as e:
    st.error(f"❌ Erro ao conectar com o BigQuery: {e}")
    st.stop()

# ====================== FILTROS LATERAIS ======================
st.sidebar.header("Filtros de Prospecção")

busca_texto = st.sidebar.text_input(
    "Buscar por Nome ou CNPJ:", 
    placeholder="Digite o nome fantasia ou CNPJ..."
)

portes_disponiveis = sorted(df["porte_descricao"].dropna().unique().tolist()) if "porte_descricao" in df.columns else []
porte_sel = st.sidebar.multiselect("Selecione o Porte da Empresa:", portes_disponiveis, default=portes_disponiveis)

setores = sorted(df["subsetor_efact"].dropna().unique().tolist()) if "subsetor_efact" in df.columns else []
setor_sel = st.sidebar.multiselect("Selecione os Setores:", setores, default=setores)

municipios = sorted(df["municipio"].dropna().unique().tolist()) if "municipio" in df.columns else []
mun_sel = st.sidebar.multiselect("Selecione os Municípios:", municipios)

# Aplicação dos filtros
df_filtrado = df.copy()

if busca_texto:
    termo = busca_texto.lower()
    mask = (
        df_filtrado["nome_fantasia"].astype(str).str.lower().str.contains(termo, na=False) |
        df_filtrado["cnpj"].astype(str).str.contains(termo, na=False)
    )
    df_filtrado = df_filtrado[mask]

if porte_sel:
    df_filtrado = df_filtrado[df_filtrado["porte_descricao"].isin(porte_sel)]
if setor_sel:
    df_filtrado = df_filtrado[df_filtrado["subsetor_efact"].isin(setor_sel)]
if mun_sel:
    df_filtrado = df_filtrado[df_filtrado["municipio"].isin(mun_sel)]

# ====================== MÉTRICAS ======================
c1, c2, c3 = st.columns(3)
c1.metric("Indústrias Mapeadas (RS)", len(df_filtrado))
c2.metric("Municípios Cobertos", df_filtrado["municipio"].nunique() if not df_filtrado.empty else 0)
c3.metric("Setores Ativos", len(setor_sel))

# ====================== MAPA ======================
def escolher_cor(subsetor):
    if not isinstance(subsetor, str):
        return "gray"
    if "Química" in subsetor or "Plástico" in subsetor: return "purple"
    elif "Metalurgia" in subsetor: return "red"
    elif "Alimentos" in subsetor: return "orange"
    elif "Celulose" in subsetor or "Papel" in subsetor: return "green"
    elif "Automotivo" in subsetor: return "cadetblue"
    elif "Têxtil" in subsetor: return "pink"
    else: return "blue"

st.subheader("Mapa de Dispersão Industrial - Rio Grande do Sul")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty:
    lat_centro = df_filtrado["latitude"].mean()
    lon_centro = df_filtrado["longitude"].mean()

mapa_efact = folium.Map(location=[-30.2, -53.5], zoom_start=7, tiles="CartoDB positron")
marker_cluster = MarkerCluster().add_to(mapa_efact)

df_amostra = df_filtrado.head(8000)

for _, row in df_amostra.iterrows():
    nome = str(row.get("nome_fantasia", "Indústria")).strip()
    if nome in ["nan", ""]: 
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

# ====================== TABELA E DOWNLOAD ======================
with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_mostrar = [c for c in ["cnpj", "nome_fantasia", "porte_descricao", 
                                   "subsetor_efact", "municipio", "latitude", "longitude"] 
                       if c in df_filtrado.columns]
    
    st.dataframe(df_filtrado[colunas_mostrar], use_container_width=True)
    
    csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Lista Filtrada (CSV)",
        data=csv_data,
        file_name="industrias_rs_real_efact.csv",
        mime="text/csv",
    )