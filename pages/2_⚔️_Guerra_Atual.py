# Este é o novo conteúdo de pages/1_⚔️_Guerra_Atual.py

import streamlit as st
from utils.coc_api import get_current_war_data
from utils.database import init_db, save_war_data # <-- ADICIONAR

# Inicializa o banco de dados no início da execução
init_db() # <-- ADICIONAR


st.set_page_config(page_title="Guerra Atual", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise da Guerra Atual")

# --- LÓGICA PRINCIPAL DA PÁGINA ---

# 1. Verifica se o usuário já fez login na página principal
# Em pages/1_⚔️_Guerra_Atual.py

# Em pages/1_⚔️_Guerra_Atual.py

if 'logged_in' in st.session_state and st.session_state['logged_in']:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.session_state['coc_email']
        coc_password = st.session_state['coc_password']

        with st.spinner("Buscando dados da guerra atual..."):
            df_war, war_summary, war_state, war_end_time = get_current_war_data(clan_tag, coc_email, coc_password)
            
            if war_state is None:
                st.info("O clã não está em uma guerra no momento.")
            else:
                st.success(f"Análise da guerra contra '{war_summary['opponent_name']}' carregada!")

                # --- EXIBIÇÃO DA DATA DA GUERRA --- # <-- ADICIONADO AQUI
                # Formata a data de término para o formato brasileiro (Dia/Mês/Ano)
                data_guerra_formatada = war_end_time.time.strftime('%d/%m/%Y')
                st.subheader(f"Data da Guerra (Término): {data_guerra_formatada}")

                st.write(f"**Estado da Guerra:** {war_state}")

                # --- PLACAR DA GUERRA ---
                col1, col2, col3 = st.columns(3)
                col1.metric(f"⭐ Placar {war_summary['clan_name']}", 
                            f"{war_summary['clan_stars']}", 
                            f"{war_summary['clan_destruction']:.2f}% de Destruição")
                
                col2.metric(f"⭐ Placar {war_summary['opponent_name']}", 
                            f"{war_summary['opponent_stars']}", 
                            f"{war_summary['opponent_destruction']:.2f}% de Destruição",
                            delta_color="inverse")

                # --- BOTÃO PARA SALVAR NO HISTÓRICO ---
                if war_state == 'warEnded':
                    if st.button("Salvar Resultado desta Guerra no Histórico"):
                        save_war_data(war_summary, df_war, war_end_time.time.isoformat())
                        st.balloons()
                        st.success("Guerra salva com sucesso no histórico!")
                
                st.header("Tabela de Ataques")
                st.dataframe(df_war)

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")
        st.warning("Ocorreu um erro. Tente fazer o login novamente na página principal.")
else:
    st.warning("🔒 Por favor, faça o login na página principal para visualizar os dados da guerra.")