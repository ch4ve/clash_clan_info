# Em utils/analysis.py, SUBSTITUA a função 'analyze_matchup_potential'

def analyze_matchup_potential(df_our_clan, df_opponent_lineup, our_clan_name, opponent_name):
    """
    Calcula o potencial de estrelas para ambos os clãs usando um modelo de pontuação heurístico.
    """
    if df_our_clan is None or df_opponent_lineup is None or 'CV' not in df_our_clan or 'CV' not in df_opponent_lineup:
        return {}

    our_attack_score = 0.0
    opponent_attack_score = 0.0
    
    df_our_clan['CV'] = pd.to_numeric(df_our_clan['CV'])
    df_opponent_lineup['CV'] = pd.to_numeric(df_opponent_lineup['CV'])
    
    num_matchups = min(len(df_our_clan), len(df_opponent_lineup))

    for i in range(num_matchups):
        our_cv = df_our_clan.iloc[i]['CV']
        opponent_cv = df_opponent_lineup.iloc[i]['CV']
        
        # --- Pontuação do nosso clã atacando ---
        diff_us = our_cv - opponent_cv
        if diff_us >= 1: our_attack_score += 2.9
        elif diff_us == 0: our_attack_score += 2.5
        elif diff_us == -1: our_attack_score += 1.8
        elif diff_us == -2: our_attack_score += 1.0
        else: our_attack_score += 0.2
        
        # --- Pontuação do oponente atacando ---
        diff_opponent = opponent_cv - our_cv
        if diff_opponent >= 1: opponent_attack_score += 2.9
        elif diff_opponent == 0: opponent_attack_score += 2.5
        elif diff_opponent == -1: opponent_attack_score += 1.8
        elif diff_opponent == -2: opponent_attack_score += 1.0
        else: opponent_attack_score += 0.2

    # Determina o vencedor e o bônus
    our_final_score = our_attack_score
    opponent_final_score = opponent_attack_score
    winner = "Empate (sem bônus)"
    
    if our_attack_score > opponent_attack_score:
        our_final_score += 10
        winner = our_clan_name
    elif opponent_attack_score > our_attack_score:
        opponent_final_score += 10
        winner = opponent_name

    return {
        "our_clan_name": our_clan_name,
        "opponent_name": opponent_name,
        "our_final_score": our_final_score,
        "opponent_final_score": opponent_final_score,
        "winner": winner
    }
