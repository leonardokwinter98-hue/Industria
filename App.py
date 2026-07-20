import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import zipfile
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Geomarketing Industrial | eFact",
    page_icon="🏭",
    layout="wide"
)

st.title("🎯 eFact - Inteligência de Expansão Comercial e Geomarketing")
st.markdown("Ferramenta de mapeamento dinâmico e prospecção de indústrias no Rio Grande do Sul.")

# 2. CARREGAMENTO DOS DADOS DIRETAMENTE DO ZIP
@st.cache_data
def carregar_dados():
    nome_zip = "dados_industrias_rs.zip"
    nome_csv = "dados_industrias_rs.csv"
    
    # Descompacta o arquivo zip presente no repositório
    if os.path.exists(nome_zip):
        with zipfile.ZipFile(nome_zip, 'r') as zip_ref:
            zip_ref.extractall(".")
            
    # Lê o arquivo CSV extraído
    if os.path.exists(nome_csv):
        return pd.read_csv(nome_csv)
    else:
        raise FileNotFoundError(f"O arquivo '{nome_csv}' não foi encontrado após a descompactação de '{nome_zip}'.")

try:
    df = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar os dados. Detalhes: {e}")
    st.stop()

# 3. FILTROS NA BARRA LATERAL
st.sidebar.header("Filtros de Prospecção")

coluna_setor = 'subst_ef' if 'subst_ef' in df.columns else 'subsetor_efact'
if coluna_setor in df.columns:
    setores_disponiveis = sorted(df[coluna_setor].dropna().unique().tolist())
    setor_selecionado = st.sidebar.multiselect("Selecione os Setores:", setores_disponiveis, default=setores_disponiveis)
else:
    setor_selecionado = []

coluna_mun = 'municipio' if 'municipio' in df.columns else 'municipio'
if coluna_mun in df.columns:
    municipios_disponiveis = sorted(df[coluna_mun].dropna().unique().tolist())
    municipio_selecionado = st.sidebar.multiselect("Selecione os Municípios:", municipios_disponiveis)
else:
    municipio_selecionado = []

df_filtrado = df.copy()
if setor_selecionado and coluna_setor in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[coluna_setor].isin(setor_selecionado)]

if municipio_selecionado and coluna_mun in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado[coluna_mun].isin(municipio_selecionado)]

# 4. MÉTRICAS EXECUTIVAS
col1, col2, col3 = st.columns(3)
col1.metric("Indústrias Filtradas para Abordagem", len(df_filtrado))
col2.metric("Municípios Abrangidos", df_filtrado[coluna_mun].nunique() if coluna_mun in df_filtrado.columns else 0)
col3.metric("Setores Ativos", len(setor_selecionado))

def escolher_cor(subsetor):
    if subsetor in ['Química, Farmo e Plástico', 'Química e Farmacêutica', 'Borracha e Plástico']: return 'purple'
    elif subsetor in ['Metalurgia e Metalmecânica']: return 'red'
    elif subsetor in ['Alimentos e Bebidas']: return 'orange'
    elif subsetor in ['Celulose, Papel e Gráfica']: return 'green'
    elif subsetor in ['Automotivo e Outros', 'Automotivo e Outros Equipamentos']: return 'cadetblue'
    else: return 'gray'

st.subheader("Mapa de Dispersão e Polos Industriais")

lat_centro, lon_centro = -30.0346, -51.2177
if not df_filtrado.empty and 'latitude' in df_filtrado.columns:
    lat_centro = df_filtrado['latitude'].mean()
    lon_centro = df_filtrado['longitude'].mean()

mapa_efact = folium.Map(location=[lat_centro, lon_centro], zoom_start=8, tiles='CartoDB positron')

for _, row in df_filtrado.iterrows():
    nome = str(row.get('nome_fnt', row.get('nome_fantasia', 'Indústria / Matriz')))
    if nome == 'nan' or nome == '': nome = "Indústria / Matriz"
    
    setor = str(row.get(coluna_setor, 'Outros'))
    mun = str(row.get(coluna_mun, 'N/D'))
    cnpj = str(row.get('cnpj', 'N/D'))
    
    html_popup = f"""
    <div style="font-family: Arial; font-size: 12px; width: 220px;">
        <b>🏢 {nome}</b><br>
        <hr style="margin: 5px 0;">
        <b>Setor eFact:</b> {setor}<br>
        <b>Município:</b> {mun}<br>
        <b>CNPJ:</b> {cnpj}
    </div>
    """
    
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=4,
        color=escolher_cor(setor),
        fill=True,
        fill_color=escolher_cor(setor),
        fill_opacity=0.7,
        popup=folium.Popup(html_popup, max_width=250),
        tooltip=f"{nome} ({mun})"
    ).add_to(mapa_efact)

st_folium(mapa_efact, width=1200, height=550)

with st.expander("Ver base de dados detalhada das indústrias filtradas"):
    colunas_exibir = [c for c in ['cnpj', 'nome_fnt', 'nome_fantasia', coluna_setor, coluna_mun] if c in df_filtrado.columns]
    st.dataframe(df_filtrado[colunas_exibir], use_container_width=True)