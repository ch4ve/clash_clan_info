# Conteúdo atualizado de pages/1_ℹ️_Info_Clã.py

import pandas as pd
import streamlit as st
from utils.coc_api import get_clan_data
# Importamos nossa nova função de ranking!
from utils.database import get_top_war_performers

st.set_page_config(page_title="Info do Clã", page_icon="ℹ️", layout="wide")
st.title("ℹ️ Visão Geral do Clã")

if 'clan_tag' in st.session_state and st.session_state['clan_tag']:
    try:
        clan_tag = st.session_state['clan_tag']
        coc_email = st.secrets["coc_email"]
        coc_password = st.secrets["coc_password"]

        with st.spinner("Buscando dados do clã..."):
            df_members, clan_name = get_clan_data(clan_tag, coc_email, coc_password)
            
            if not df_members.empty:
                st.success(f"Dados do clã '{clan_name}' carregados com sucesso!")
                
                st.header("Membros Atuais")
                st.dataframe(df_members, hide_index=True)

                st.divider() # Adiciona uma linha divisória

                # --- NOVO BLOCO: DESTAQUES DO CLÃ ---
                st.header("⭐ Destaques do Clã")
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🏆 Top 5 - Últimas 5 Guerras")
                    df_top5_wars = get_top_war_performers()

                    if not df_top5_wars.empty:
                        # Para pegar o CV atual, juntamos o ranking com a lista de membros
                        df_top5_wars_with_cv = pd.merge(
                            df_top5_wars,
                            df_members[['Nome', 'CV']],
                            on='Nome',
                            how='left'
                        ).fillna(0) # Preenche CV com 0 se o membro saiu do clã

                        # Formata a coluna de destruição para exibição
                        df_top5_wars_with_cv['Total Destruição'] = df_top5_wars_with_cv['Total Destruição'].apply(lambda x: f"{x}%")
                        
                        # Define a ordem final das colunas para exibir
                        display_columns = ['Nome', 'CV', 'Total Estrelas', 'Total Destruição']
                        
                        st.dataframe(df_top5_wars_with_cv[display_columns], hide_index=True)
                    else:
                        st.info("Não há dados de guerras suficientes no histórico para gerar um ranking.")
                
                with col2:
                    st.subheader("🥇 Top 5 - Última Liga (CWL)")
                    st.info("Funcionalidade em desenvolvimento...")

            else:
                st.error("Não foi possível carregar os dados do clã.")
    except Exception as e:
        st.error(f"Erro ao buscar dados da API: {e}")

else:
    st.warning("🔒 Por favor, faça o login para visualizar as informações do clã.")
    st.page_link("login.py", label="Ir para a página de Login", icon="🔑")


