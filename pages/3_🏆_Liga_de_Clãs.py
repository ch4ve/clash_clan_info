# Conteúdo RESTAURADO de pages/3_🏆_Liga_de_Clãs.py

import streamlit as st
from utils.coc_api import get_cwl_data

st.set_page_config(page_title="Liga de Clãs (CWL)", page_icon="🏆", layout="wide")
st.title("🏆 Resumo da Liga de Guerras de Clãs (CWL)")

# Verifica se o usuário já fez login na página principal
if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        # Pega as credenciais da "memória" (Session State) e dos segredos
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        st.info("A análise da CWL pode ser demorada, pois busca os dados de até 7 dias de guerra.")
        if st.button("Analisar Desempenho da Liga"):
            with st.spinner("Buscando e consolidando dados de todos os dias da CWL..."):
                df_summary, season = get_cwl_data(clan_tag, coc_email, coc_password)

                if season is None:
                    st.info(f"O clã ({clan_tag}) não parece estar participando de uma CWL no momento.")
                elif df_summary.empty:
                    st.warning(f"CWL da temporada '{season}' encontrada, mas nenhum ataque foi registrado ainda.")
                else:
                    st.success(f"Relatório da CWL da temporada '{season}' gerado!")
                    st.header("Resumo de Desempenho dos Membros")
                    st.dataframe(df_summary, hide_index=True)

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")
        st.warning("Ocorreu um erro. Tente fazer o login novamente na página principal.")

else:
    # Se não estiver logado, mostra uma mensagem
    st.warning("🔒 Por favor, faça o login na página principal para visualizar os dados da CWL.")
    st.page_link("login.py", label="Ir para a página de Login", icon="🔑")

