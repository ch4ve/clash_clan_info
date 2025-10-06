# Conteúdo ATUALIZADO de utils/analysis.py

import pandas as pd
from collections import defaultdict
from . import database # Importa nosso módulo de banco de dados

def analyze_matchup_potential(df_our_clan, df_opponent_lineup, our_clan_name, opponent_name):
    """
    Calcula o potencial de estrelas para ambos os clãs em um confronto,
    determina o vencedor e aplica o bônus de vitória.
    """
    if df_our_clan is None or df_opponent_lineup is None or 'CV' not in df_our_clan or 'CV' not in df_opponent_lineup:
        return {}

    our_attack_stars = 0
    opponent_attack_stars = 0
    
    df_our_clan['CV'] = pd.to_numeric(df_our_clan['CV'])
    df_opponent_lineup['CV'] = pd.to_numeric(df_opponent_lineup['CV'])
    
    num_matchups = min(len(df_our_clan), len(df_opponent_lineup))

    for i in range(num_matchups):
        our_cv = df_our_clan.iloc[i]['CV']
        opponent_cv = df_opponent_lineup.iloc[i]['CV']
        
        # Potencial do nosso clã (Lado Direito) atacando o oponente (Lado Esquerdo)
        diff_us = our_cv - opponent_cv
        if diff_us >= 0: our_attack_stars += 3
        elif diff_us == -1: our_attack_stars += 2
        elif diff_us == -2: our_attack_stars += 1
        
        # Potencial do oponente (Lado Esquerdo) atacando nosso clã (Lado Direito)
        diff_opponent = opponent_cv - our_cv
        if diff_opponent >= 0: opponent_attack_stars += 3
        elif diff_opponent == -1: opponent_attack_stars += 2
        elif diff_opponent == -2: opponent_attack_stars += 1

    # Determina o vencedor e o bônus
    our_final_score = our_attack_stars
    opponent_final_score = opponent_attack_stars
    winner = "Empate (sem bônus)"
    
    if our_attack_stars > opponent_attack_stars:
        our_final_score += 10
        winner = our_clan_name
    elif opponent_attack_stars > our_attack_stars:
        opponent_final_score += 10
        winner = opponent_name

    return {
        "our_clan_name": our_clan_name,
        "opponent_name": opponent_name,
        "our_final_score": our_final_score,
        "opponent_final_score": opponent_final_score,
        "winner": winner
    }

def get_top_war_performers(limit=5):
    # (Esta função continua a mesma de antes)
    war_data_rows = database.get_last_n_wars(limit=limit)
    if not war_data_rows: return pd.DataFrame()
    player_stats = defaultdict(lambda: {'Total Estrelas': 0, 'Total Destruição': 0, 'Guerras': 0})
    for war_row in war_data_rows:
        df_war = pd.read_json(war_row[0], orient='split')
        for _, player_row in df_war.iterrows():
            if 'Nome' in player_row and 'Estrelas Totais' in player_row:
                player_name = player_row['Nome']
                player_stats[player_name]['Total Estrelas'] += player_row['Estrelas Totais']
                player_stats[player_name]['Total Destruição'] += int(str(player_row.get('Destruição Total', '0%')).replace('%', ''))
                player_stats[player_name]['Guerras'] += 1
    if not player_stats: return pd.DataFrame()
    df_summary = pd.DataFrame.from_dict(player_stats, orient='index').reset_index().rename(columns={'index': 'Nome'})
    df_summary = df_summary.sort_values(by=['Total Estrelas', 'Total Destruição'], ascending=[False, False])
    return df_summary.head(5)
