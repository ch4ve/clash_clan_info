# Conteúdo de pages/3_📜_Histórico_de_Guerras.py (atualizado)

import streamlit as st
from utils.database import init_db, get_war_history_list, get_war_by_id

# Inicializa o banco de dados
init_db()

st.set_page_config(page_title="Histórico de Guerras", page_icon="📜", layout="wide")
st.title("📜 Histórico de Guerras")

if 'logged_in' in st.session_state and st.session_state['logged_in']:
    war_list = get_war_history_list()
    
    if not war_list:
        st.info("Nenhuma guerra foi salva no histórico ainda.")
    else:
        # <<<--- MUDANÇA PRINCIPAL AQUI ---<<<
        # Agora usamos a coluna de data (war[2]) que é mais limpa, em vez de fatiar o texto
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
    st.warning("🔒 Por favor, faça o login na página principal para ver o histórico.")