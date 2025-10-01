# Novo conteúdo de pages/4_📜_Histórico_de_Guerras.py

import streamlit as st
from utils.database import init_db, get_war_history_list, get_war_by_id

init_db()

st.set_page_config(page_title="Histórico de Guerras", page_icon="📜", layout="wide")
st.title("📜 Histórico de Guerras")

# Esta página não precisa da API, mas só faz sentido se um clã já foi analisado.
# Por consistência, vamos usar a mesma verificação.
if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    
    st.info("Esta página exibe apenas as guerras que foram salvas manualmente através da página 'Guerra Atual'.")
    war_list = get_war_history_list()
    
    if not war_list:
        st.warning("Nenhuma guerra foi salva no histórico ainda.")
    else:
        option_map = {f"vs. {war[1]} ({war[2]})": war[0] for war in war_list if war[2]}
        
        selected_option = st.selectbox(
            "Selecione uma guerra do histórico para visualizar:",
            options=option_map.keys()
        )
        
        if selected_option:
            war_id = option_map[selected_option]
            summary, df_attacks = get_war_by_id(war_id)
            
            st.header(f"Detalhes da Guerra contra {summary['opponent_name']}")
            col1, col2 = st.columns(2)
            col1.metric("⭐ Nosso Placar", f"{summary['clan_stars']}", f"{summary['clan_destruction']:.2f}%")
            col2.metric(f"⭐ Placar Oponente", f"{summary['opponent_stars']}", delta_color="inverse")
            st.dataframe(df_attacks)
else:
    # Se nenhuma tag foi definida, instrui o usuário a voltar
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
