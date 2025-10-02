# Conteúdo NOVO e AUTOMÁTICO de pages/2_⚔️_Guerra_Atual.py

import streamlit as st
from utils.coc_api import get_current_war_data
# Importamos a nova função de verificação
from utils.database import init_db, save_war_data, is_war_saved

init_db()

st.set_page_config(page_title="Guerra Atual", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise da Guerra Atual")

if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        with st.spinner("Buscando dados da guerra atual..."):
            df_full_data, df_display_data, war_summary, war_state, war_end_time = get_current_war_data(clan_tag, coc_email, coc_password)
            
            if war_state is None:
                st.info(f"O clã ({clan_tag}) não está em uma guerra no momento.")
            else:
                st.success(f"Análise da guerra contra '{war_summary['opponent_name']}' carregada!")
                data_guerra_formatada = war_end_time.time.strftime('%d/%m/%Y')
                st.subheader(f"Data da Guerra (Término): {data_guerra_formatada}")
                st.write(f"**Estado da Guerra:** {war_state}")

                # (O código do placar continua o mesmo...)
                col1, col2, col3 = st.columns(3)
                col1.metric(f"⭐ Placar {war_summary['clan_name']}", f"{war_summary['clan_stars']}", f"{war_summary['clan_destruction']:.2f}% de Destruição")
                col2.metric(f"⭐ Placar {war_summary['opponent_name']}", f"{war_summary['opponent_stars']}", f"{war_summary['opponent_destruction']:.2f}% de Destruição", delta_color="inverse")

                st.header("Tabela de Ataques")
                st.dataframe(df_display_data, hide_index=True)
                
                st.divider() # Linha divisória para separar

                # --- LÓGICA DE SALVAMENTO AUTOMÁTICO ---
                # 1. Verifica se a guerra terminou
                if war_state == 'warEnded':
                    war_id = war_end_time.time.isoformat()
                    # 2. Verifica se a guerra já NÃO foi salva
                    if not is_war_saved(war_id):
                        st.info("Detectamos que a guerra terminou! Salvando resultado no histórico...")
                        save_war_data(war_summary, df_full_data, war_id)
                        st.success("Resultado da guerra salvo automaticamente no histórico! ✨")
                        st.balloons()
                    else:
                        st.info("O resultado desta guerra já está salvo no histórico.")

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

else:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("login.py", label="Ir para a página principal", icon="🏠")

