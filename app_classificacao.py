import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from io import BytesIO
from PIL import Image

# Função para calcular RFV (Recência, Frequência, Valor)
def calcula_rfv(data):
    # Calcula a recência em relação à data atual
    max_date = max(data['DiaCompra'])
    data['Recencia'] = (max_date - data['DiaCompra']).dt.days

    # Agrupa por ID_cliente e calcula Frequência e Valor
    rfv_data = data.groupby('ID_cliente').agg({
        'Recencia': 'min',
        'CodigoCompra': 'count',
        'ValorTotal': 'sum'
    }).reset_index()

    # Renomeia as colunas
    rfv_data.columns = ['ID_cliente', 'Recencia', 'Frequencia', 'Valor']

    return rfv_data

# Função para classificar os clientes usando K-means
def classifica_cliente(data):
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data[['Recencia', 'Frequencia', 'Valor']])
    
    kmeans = KMeans(n_clusters=3, random_state=42)
    data['Cluster'] = kmeans.fit_predict(data_scaled)
    
    return data

# Define as URL do ícone da página
url_icone = "https://raw.githubusercontent.com/AdiltonCarvalho/Analise_RFV/main/icone_velocimetro.png"

# Faz o download do ícone usando requests
response = requests.get(url_icone)
if response.status_code == 200:
    # Lê o conteúdo da imagem
    image = Image.open(BytesIO(response.content))
    
    # Configuração da página do Streamlit
    st.set_page_config(page_title='Análise RFV', page_icon=image, layout='wide', initial_sidebar_state='expanded')
else:
    # Configuração da página do Streamlit com ícone padrão
    st.set_page_config(page_title='Análise de Telemarketing', layout='wide', initial_sidebar_state='expanded')