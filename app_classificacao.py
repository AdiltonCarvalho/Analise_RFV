import streamlit as st
import pandas as pd
import requests
import base64
import plotly.express as px
from datetime import datetime
from io import BytesIO, StringIO
from PIL import Image

# Função para calcular RFV (Recência, Frequência, Valor)
def calcula_rfv(data):
    # Encontrar a data atual
    data_atual = datetime.now()

    # Encontrar a data da última compra para cada cliente
    ultima_compra = data.groupby('ID_cliente')['DiaCompra'].max().reset_index()
    
    # Calcular a recência em relação à data atual e à última compra
    ultima_compra['Recencia'] = (data_atual - ultima_compra['DiaCompra']).dt.days

    # Merge para adicionar a recência ao DataFrame principal
    data = pd.merge(data, ultima_compra[['ID_cliente', 'Recencia']], on='ID_cliente', how='left')

    # Agrupa por ID_cliente e calcula Frequência e Valor
    rfv_data = data.groupby('ID_cliente').agg({
        'Recencia': 'min',
        'CodigoCompra': 'count',
        'ValorCompra': 'sum'
    }).reset_index()

    # Renomeia as colunas
    rfv_data.columns = ['ID_cliente', 'Recência', 'Frequência', 'Valor Total']

    return rfv_data

# Função para classificar a recência por quartil 
def recencia_classe(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
        return 'C'
    else:
        return 'D'

# Função para classificar a frequência e o valor por quartil
def freq_val_classe(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'
    
# Função para download em excel
def download_excel(dataframe, filename, sheet_name='Sheet1'):
    output = BytesIO()
    excel_writer = pd.ExcelWriter(output, engine='xlsxwriter')
    dataframe.to_excel(excel_writer, sheet_name=sheet_name, index=True)
    excel_writer.close()
    excel_data_excel = output.getvalue()
    b64 = base64.b64encode(excel_data_excel).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">Download Excel</a>'
    return href

# Função para aplicar filtros multiseleção
def multiselect_filter(df, column, selected_values):
    if not selected_values:
        return df
    return df[df[column].isin(selected_values)]

# Função principal
def main():
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
        st.set_page_config(page_title='Análise RFV', layout='wide', initial_sidebar_state='expanded')
        
    # Caminho para a imagem
    url_imagem = 'https://raw.githubusercontent.com/AdiltonCarvalho/Analise_RFV/main/imagem_velocimetro.png'

    # Verifica se a imagem do menu está disponível
    response = requests.head(url_imagem)
    if response.status_code == 200:    
        # Faz o download e exibe a imagem
        image_response = requests.get(url_imagem)
        image = Image.open(BytesIO(image_response.content))
        st.sidebar.image(image, use_column_width=True)
    else:
        st.sidebar.warning('Imagem não encontrada')
        
    # Título da aplicação
    # Utiliza HTML para centralizar o título
    st.markdown("""<h1 style='text-align: center;'>Análise de Clientes - RFV (Recência, Frequência e Valor)</h1>""", unsafe_allow_html=True)
    st.markdown("---")
        
    # Seção para carregar a base de dados
    st.sidebar.header("Carregar Base de Dados")
    
    # Caminho para a base de dados
    url_csv = 'https://raw.githubusercontent.com/AdiltonCarvalho/Analise_RFV/main/dados_input1.csv'

   # Obtém o conteúdo do arquivo CSV usando requests
    response = requests.get(url_csv)

    # Verifica se a resposta foi bem-sucedida
    if response.status_code == 200:
        # Lê os dados do CSV
        decoded_content = response.content.decode('utf-8')
        df = pd.read_csv(StringIO(decoded_content), sep=',')
        df_copia = df.copy()
        df_copia['DiaCompra'] = pd.to_datetime(df_copia['DiaCompra'])
        # Carrega a base de dados
        if df_copia is not None:
            # Calcula RFV
            rfv_data = calcula_rfv(df_copia)
        
            # Calcula os quartis para Recência, Frequência e Valor Total
            quartis = rfv_data.quantile(q=[0.25, 0.5, 0.75])
            quartis.to_dict()

            # Aplica a função recencia_classe para criar a coluna 'R_Quartil' com base nos quartis
            rfv_data['R_Quartil'] = rfv_data['Recência'].apply(recencia_classe, args=('Recência', quartis))

            # Aplica a função freq_val_classe para criar a coluna 'F_Quartil' com base nos quartis
            rfv_data['F_Quartil'] = rfv_data['Frequência'].apply(freq_val_classe, args=('Frequência', quartis))

            # Aplica a função freq_val_classe para criar a coluna 'V_Quartil' com base nos quartis
            rfv_data['V_Quartil'] = rfv_data['Valor Total'].apply(freq_val_classe, args=('Valor Total', quartis))

            # Cria uma cópia dos dados finais antes de adicionar a coluna 'RFV_Score'
            rfv_data_final = rfv_data.copy()

            # Calcula a pontuação RFV somando as colunas 'R_Quartil', 'F_Quartil' e 'V_Quartil'
            rfv_data_final['RFV_Score'] = rfv_data['R_Quartil'] + rfv_data['F_Quartil'] + rfv_data['V_Quartil']
        
            # Título do menu
            st.sidebar.title('Menu')
                          
            # Filtro por recência
            recencia_lista = rfv_data_final['R_Quartil'].unique().tolist()
            recencia_selecao = st.sidebar.multiselect('Filtrar Recência', recencia_lista)
        
            # Filtro por frequência
            frequencia_lista = rfv_data_final['F_Quartil'].unique().tolist()
            frequencia_selecao = st.sidebar.multiselect('Filtrar Frequência', frequencia_lista)
        
            # Filtro por valor
            valor_lista = rfv_data_final['V_Quartil'].unique().tolist()
            valor_selecao = st.sidebar.multiselect('Filtrar Valor', valor_lista)
        
            # Filtro por score
            score_lista = rfv_data_final['RFV_Score'].unique().tolist()
            score_selecao = st.sidebar.multiselect('Filtrar Score', score_lista)

            # Botão para aplicar os filtros
            aplicar_filtro = st.sidebar.button('Aplicar')
        
            # Exibe o dataframe df com dados originais
            st.write("### Dados Originais")
            # Contagem de linhas do dataframe df sem o cabeçalho
            st.write(f"Total de linhas: {df.shape[0]}")
            total_dias = (df_copia['DiaCompra'].max() - df_copia['DiaCompra'].min()).days
            st.write(f"Total de dias: {total_dias}")
            st.write(df)
        
            # Exibe o datafame rfv_data com avaliação RFV    
            st.markdown("---")
            st.write("### Resultado da Avaliação RFV")
            # Contagem de linhas do dataframe rfv_data sem o cabeçalho
            st.write(f"Total de linhas: {rfv_data.shape[0]}")
            st.write(rfv_data)
        
            st.markdown("---")
            # Divide a tela em duas colunas
            col1, col2 = st.columns(2)
        
            # Exibe o dataframe rfv_data_final classificado em quartis
            col1.write("### Resultado da Classificação RFV")
            col1.write(rfv_data_final)
   
            # Cria um link para download do dataframe rfv_data_final
            excel_data_2 = rfv_data_final
            excel_href_2 = download_excel(excel_data_2, 'Clientes classificados')
            col1.markdown(excel_href_2, unsafe_allow_html=True)
            
            # Cria um relatório na segunda coluna com valores máximos, mínimos e médios do dataframe rfv_data_final
            col2.write("### Relatório da Classificação RFV")
            col2.write(f"Total de linhas: {rfv_data_final.shape[0]}")
            col2.write(f"Total de grupos RFV_Score: {rfv_data_final['RFV_Score'].nunique()}")
            col2.write(f"Maior Recência: {rfv_data_final['Recência'].max()}")
            col2.write(f"Menor Recência: {rfv_data_final['Recência'].min()}")
            col2.write(f"Média Recência: {round (rfv_data_final['Recência'].mean(), 2)}")
            col2.write(f"Maior Frequência: {rfv_data_final['Frequência'].max()}")
            col2.write(f"Menor Frequência: {rfv_data_final['Frequência'].min()}")
            col2.write(f"Média Frequência: {round (rfv_data_final['Frequência'].mean(), 2)}")
            col2.write(f"Maior Valor Total: {rfv_data_final['Valor Total'].max()}")
            col2.write(f"Menor Valor Total: {rfv_data_final['Valor Total'].min()}")
            col2.write(f"Média Valor Total: {round (rfv_data_final['Valor Total'].mean(), 2)}")
        
            # Encadeamento de métodos para aplicar os filtros
            if aplicar_filtro:
                if recencia_selecao or frequencia_selecao or valor_selecao:
                    # Inativa o filtro RFV_Score se qualquer outro filtro estiver preenchido
                    rfv_data_final = (rfv_data_final
                          .pipe(multiselect_filter, 'R_Quartil', recencia_selecao)
                          .pipe(multiselect_filter, 'F_Quartil', frequencia_selecao)
                          .pipe(multiselect_filter, 'V_Quartil', valor_selecao)
                          .pipe(multiselect_filter, 'RFV_Score', []))
                elif score_selecao:
                    # Inativa os demais filtros se o RFV_Score estiver preenchido
                    rfv_data_final = (rfv_data_final
                          .pipe(multiselect_filter, 'R_Quartil', [])
                          .pipe(multiselect_filter, 'F_Quartil', [])
                          .pipe(multiselect_filter, 'V_Quartil', [])
                          .pipe(multiselect_filter, 'RFV_Score', score_selecao))
                else:
                    # Mantém todos os filtros ativos se nenhum filtro estiver preenchido
                    rfv_data_final = (rfv_data_final
                          .pipe(multiselect_filter, 'R_Quartil', recencia_selecao)
                          .pipe(multiselect_filter, 'F_Quartil', frequencia_selecao)
                          .pipe(multiselect_filter, 'V_Quartil', valor_selecao)
                          .pipe(multiselect_filter, 'RFV_Score', []))               
        
            # Exibe os resultados da classificação em quartis
            col1.markdown("---")        
            col1.write("### Resultado da Classificação RFV Filtrado")
            col1.write(rfv_data_final)
        
            # Cria um link para download da base filtrada
            excel_data_1 = rfv_data_final
            excel_href_1 = download_excel(excel_data_1, 'Clientes filtrados')
            col1.markdown(excel_href_1, unsafe_allow_html=True)
        
            # Cria um relatório na segunda coluna com valores máximos, mínimos e médios RFV filtrados
            col2.markdown("---")
            col2.write("### Relatório da Classificação RFV Filtrado")
            col2.write(f"Total de linhas: {rfv_data_final.shape[0]}")
            col2.write(f"Total de grupos RFV_Score: {rfv_data_final['RFV_Score'].nunique()}")
            col2.write(f"Maior Recência: {rfv_data_final['Recência'].max()}")
            col2.write(f"Menor Recência: {rfv_data_final['Recência'].min()}")
            col2.write(f"Média Recência: {round (rfv_data_final['Recência'].mean(), 2)}")
            col2.write(f"Maior Frequência: {rfv_data_final['Frequência'].max()}")
            col2.write(f"Menor Frequência: {rfv_data_final['Frequência'].min()}")
            col2.write(f"Média Frequência: {round (rfv_data_final['Frequência'].mean(), 2)}")
            col2.write(f"Maior Valor Total: {round (rfv_data_final['Valor Total'].max(), 2)}")
            col2.write(f"Menor Valor Total: {round (rfv_data_final['Valor Total'].min(), 2)}")
            col2.write(f"Média Valor Total: {round (rfv_data_final['Valor Total'].mean(), 2)}")
        
            # Adiciona um gráfico de barras interativo usando plotly.express
            fig1 = px.bar(rfv_data_final['RFV_Score'].value_counts(), title='Contagem de Grupos RFV_Score')
            fig1.update_layout(xaxis_title='', yaxis_title='')
            st.plotly_chart(fig1, use_container_width=True)

            # Adiciona um gráfico de dispersão (scatter plot) interativo usando plotly.express
            fig2 = px.scatter(rfv_data_final, x='Recência', y='Valor Total', color='RFV_Score', title='Relação entre Recência, Valor Total e RFV_Score')
            st.plotly_chart(fig2, use_container_width=True)
        
            # Adiciona um gráfico de dispersão (scatter plot) interativo usando plotly.express
            fig3 = px.scatter(rfv_data_final, x='Frequência', y='Valor Total', color='RFV_Score', title='Relação entre Frequência, Valor Total e RFV_Score')
            st.plotly_chart(fig3, use_container_width=True)      
    
if __name__ == "__main__":
    main()