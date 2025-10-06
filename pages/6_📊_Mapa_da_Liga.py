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
            # (Lógica de busca dos dados continua a mesma)
            clan_tag = st.session_state['clan_tag']
            coc_email = st.secrets["coc_email"]
            coc_password = st.secrets["coc_password"]
            with st.spinner("Espionando clãs e simulando resultados..."):
                df_our_clan, league_preview, our_clan_name = generate_full_league_preview(clan_tag, coc_email, coc_password)

            if league_preview is None:
                st.error(f"Não foi possível gerar o mapa da liga: {df_our_clan}")
            else:
                st.success("Mapa estratégico completo gerado com sucesso!")
                
                grand_total_stars = 0
                all_analyses = []
                for matchup in league_preview:
                    df_predicted_opponent = matchup['predicted_lineup']
                    analysis_result = {}
                    if "Erro" not in df_predicted_opponent.columns:
                        analysis_result = analyze_matchup_potential(df_our_clan, df_predicted_opponent, our_clan_name, matchup['opponent_name'])
                        if 'our_final_score' in analysis_result:
                            grand_total_stars += analysis_result['our_final_score']
                    all_analyses.append({"analysis": analysis_result, "opponent_df": df_predicted_opponent})

                # --- EXIBIÇÃO DOS RESULTADOS ---
                st.header(f"Previsão de Estrelas Totais na Liga: {grand_total_stars:.1f}")
                st.caption("Cálculo baseado em um modelo heurístico, sem falha humana e com bônus de vitória (+10).")
                
                for item in all_analyses:
                    analysis = item['analysis']
                    df_opponent = item['opponent_df']
                    st.divider()
                    if not analysis:
                        st.header(f"Previsão: {our_clan_name} vs Oponente Desconhecido")
                        st.dataframe(df_opponent, hide_index=True)
                        continue

                    st.header(f"Previsão: {analysis['our_clan_name']} vs {analysis['opponent_name']}")

                    # --- MÉTRICAS COM CASAS DECIMAIS ---
                    col_a, col_b, col_c = st.columns(3)
                    col_a.metric(f"Pontuação {analysis['our_clan_name']}", f"{analysis['our_final_score']:.1f} ⭐")
                    col_b.metric(f"Pontuação {analysis['opponent_name']}", f"{analysis['opponent_final_score']:.1f} ⭐")
                    col_c.info(f"Vencedor Previsto: {analysis['winner']}")

                    # (O resto da página, com as tabelas, continua igual)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Nossa Escalação Atual"); st.dataframe(df_our_clan, hide_index=True)
                    with col2:
                        st.subheader(f"Escalação Provável de '{analysis['opponent_name']}'"); st.dataframe(df_opponent, hide_index=True)
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao gerar o mapa: {e}")
