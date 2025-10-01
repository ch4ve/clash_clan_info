# Este é o conteúdo de pages/2_🏆_Liga_de_Clãs.py

import streamlit as st
from utils.coc_api import get_cwl_data # Importa nossa nova função

st.set_page_config(page_title="Liga de Clãs (CWL)", page_icon="🏆", layout="wide")
st.title("🏆 Análise da Liga de Guerras de Clãs (CWL)")

# Verifica se o usuário já fez login na página principal
if 'logged_in' in st.session_state and st.session_state['logged_in']:
    try:
        # Pega as credenciais da "memória" (Session State)
        clan_tag = st.session_state['clan_tag']
        coc_email = st.session_state['coc_email']
        coc_password = st.session_state['coc_password']

        # Botão para iniciar a análise
        if st.button("Analisar Desempenho da Liga"):
            with st.spinner("Buscando e consolidando dados de todos os dias da CWL... Isso pode ser demorado."):
                df_summary, season = get_cwl_data(clan_tag, coc_email, coc_password)

                if season is None:
                    st.info("O clã não parece estar participando de uma CWL no momento.")
                elif df_summary.empty:
                    st.warning(f"CWL da temporada '{season}' encontrada, mas nenhum ataque foi registrado ainda.")
                else:
                    st.success(f"Relatório da CWL da temporada '{season}' gerado!")
                    
                    st.header("Resumo de Desempenho dos Membros")
                    # Exibe o DataFrame consolidado
                    st.dataframe(df_summary)

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")
        st.warning("Ocorreu um erro. Tente fazer o login novamente na página principal.")

else:
    # Se não estiver logado, mostra uma mensagem
    st.warning("🔒 Por favor, faça o login na página principal ('app') para visualizar os dados da CWL.")