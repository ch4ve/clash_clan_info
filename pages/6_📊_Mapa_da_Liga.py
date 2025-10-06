# Conteúdo ATUALIZADO de pages/6_📊_Mapa_da_Liga.py

import streamlit as st
from utils.coc_api import generate_full_league_preview
from utils.analysis import analyze_matchup_potential

st.set_page_config(page_title="Mapa da Liga", page_icon="📊", layout="wide")
st.title("📊 Mapa Estratégico Completo da Liga")

if 'clan_tag' not in st.session_state or not st.session_state['clan_tag']:
    st.warning("⬅️ Por favor, insira uma tag de clã na página principal para começar.")
else:
    st.warning("⚠️ **Atenção:** A geração deste mapa completo pode levar vários minutos.")

    if st.button("Gerar Mapa Completo da Liga"):
        try:
            clan_tag = st.session_state['clan_tag']
            coc_email = st.secrets["coc_email"]
            coc_password = st.secrets["coc_password"]

            with st.spinner("Espionando todos os clãs do grupo e calculando potenciais..."):
                df_our_clan, league_preview, our_clan_name = generate_full_league_preview(clan_tag, coc_email, coc_password)

                if league_preview is None:
                    st.error(f"Não foi possível gerar o mapa da liga: {df_our_clan}")
                else:
                    st.success("Mapa estratégico completo gerado com sucesso!")
                    
                    # --- LÓGICA DE CÁLCULO TOTAL ---
                    grand_total_stars = 0
                    matchup_analyses = []
                    
                    for matchup in league_preview:
                        opponent_name = matchup['opponent_name']
                        df_predicted_opponent = matchup['predicted_lineup']
                        
                        analysis_result = {}
                        if "Erro" not in df_predicted_opponent.columns:
                            analysis_result = analyze_matchup_potential(df_our_clan, df_predicted_opponent, our_clan_name, opponent_name)
                            if 'our_final_score' in analysis_result:
                                grand_total_stars += analysis_result['our_final_score']
                        
                        matchup_analyses.append({
                            "analysis": analysis_result,
                            "opponent_df": df_predicted_opponent
                        })

                    # --- EXIBIÇÃO DOS RESULTADOS ---
                    st.header(f"Previsão de Estrelas Totais na Liga: {grand_total_stars}")
                    st.caption("Cálculo baseado em espelhos, sem falha humana e com bônus de vitória (+10). Empates não dão bônus.")
                    
                    for item in matchup_analyses:
                        analysis = item['analysis']
                        df_opponent = item['opponent_df']
                        
                        st.divider()

                        if not analysis:
                            st.header(f"Previsão: {our_clan_name} vs Oponente Desconhecido")
                            st.dataframe(df_opponent, hide_index=True)
                            continue

                        st.header(f"Previsão: {analysis['our_clan_name']} vs {analysis['opponent_name']}")

                        # Métricas por guerra
                        col_a, col_b, col_c = st.columns(3)
                        col_a.metric(f"Estrelas {analysis['our_clan_name']} (Lado Direito)", f"{analysis['our_final_score']} ⭐")
                        col_b.metric(f"Estrelas {analysis['opponent_name']} (Lado Esquerdo)", f"{analysis['opponent_final_score']} ⭐")
                        col_c.info(f"Vencedor: {analysis['winner']}")

                        # Tabelas de escalação
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("Nossa Escalação Atual")
                            st.dataframe(df_our_clan, hide_index=True)
                        with col2:
                            st.subheader(f"Escalação Provável de '{analysis['opponent_name']}'")
                            st.dataframe(df_opponent, hide_index=True)

        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao gerar o mapa: {e}")
