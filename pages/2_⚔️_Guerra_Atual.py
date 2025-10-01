# Novo conteúdo de pages/2_⚔️_Guerra_Atual.py

import streamlit as st
from utils.coc_api import get_current_war_data
from utils.database import init_db, save_war_data

init_db()

st.set_page_config(page_title="Guerra Atual", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise da Guerra Atual")

# Verifica se uma tag de clã foi inserida na página principal
if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        # Pega a tag da memória e as credenciais dos segredos
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        with st.spinner("Buscando dados da guerra atual..."):
            df_war, war_summary, war_state, war_end_time = get_current_war_data(clan_tag, coc_email, coc_password)
            
            if war_state is None:
                st.info(f"O clã ({clan_tag}) não está em uma guerra no momento.")
            else:
                st.success(f"Análise da guerra contra '{war_summary['opponent_name']}' carregada!")
                data_guerra_formatada = war_end_time.time.strftime('%d/%m/%Y')
                st.subheader(f"Data da Guerra (Término): {data_guerra_formatada}")
                st.write(f"**Estado da Guerra:** {war_state}")

                col1, col2, col3 = st.columns(3)
                col1.metric(f"⭐ Placar {war_summary['clan_name']}", f"{war_summary['clan_stars']}", f"{war_summary['clan_destruction']:.2f}% de Destruição")
                col2.metric(f"⭐ Placar {war_summary['opponent_name']}", f"{war_summary['opponent_stars']}", f"{war_summary['opponent_destruction']:.2f}% de Destruição", delta_color="inverse")

                if war_state == 'warEnded':
                    if st.button("Salvar Resultado desta Guerra no Histórico"):
                        save_war_data(war_summary, df_war, war_end_time.time.isoformat())
                        st.balloons()
                        st.success("Guerra salva com sucesso no histórico!")
                
                st.header("Tabela de Ataques")
                st.dataframe(df_war)

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

else:
    # Se nenhuma tag foi definida, instrui o usuário a voltar
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
