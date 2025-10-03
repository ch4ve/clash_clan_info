# Conteúdo NOVO e REFATORADO de pages/2_⚔️_Guerra_Atual.py

import streamlit as st
# Importamos nossos novos módulos de serviço!
from services import api_client, database

# A função de inicialização do banco agora é chamada a partir do módulo
database.init_db()

st.set_page_config(page_title="Guerra Atual", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise da Guerra Atual")

if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        clan_tag = st.session_state['clan_tag']

        with st.spinner("Buscando dados da guerra atual..."):
            # Usamos a função do nosso novo api_client
            df_full_data, df_display_data, war_summary, war_state, war_end_time = api_client.get_current_war_data(clan_tag)
            
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

                st.header("Tabela de Ataques")
                st.dataframe(df_display_data, hide_index=True)
                
                st.divider()

                if war_state == 'warEnded':
                    war_id = war_end_time.time.isoformat()
                    # A função de verificação agora vem do módulo de database
                    if not database.is_war_saved(war_id):
                        st.info("Detectamos que a guerra terminou! Salvando resultado no histórico...")
                        # A função de salvar agora vem do módulo de database
                        database.save_war_data(war_summary, df_full_data, war_id)
                        st.success("Resultado da guerra salvo automaticamente no histórico! ✨")
                        st.balloons()
                    else:
                        st.info("O resultado desta guerra já está salvo no histórico.")

    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

else:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
    st.page_link("app.py", label="Ir para a página principal", icon="🏠")
