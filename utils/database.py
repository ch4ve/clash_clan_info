# Conteúdo COMPLETO e CORRIGIDO de utils/database.py

import streamlit as st
import pandas as pd
import json
import psycopg2
from collections import defaultdict

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados PostgreSQL usando os segredos."""
    conn = psycopg2.connect(st.secrets["db_connection_string"])
    return conn

def init_db():
    """Cria a tabela 'wars' no banco de dados PostgreSQL, se não existir."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wars (
                    war_id TEXT PRIMARY KEY,
                    opponent_name TEXT NOT NULL,
                    clan_stars INTEGER,
                    opponent_stars INTEGER,
                    clan_destruction REAL,
                    data_json TEXT NOT NULL,
                    war_date DATE
                )
            """)
        conn.commit()

def save_war_data(war_summary, df_attacks, war_end_time_iso):
    """Salva os dados de uma guerra no banco de dados PostgreSQL."""
    df_json = df_attacks.to_json(orient='split')
    war_date_formatted = war_end_time_iso.split('T')[0]
    
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO wars (war_id, opponent_name, clan_stars, opponent_stars, clan_destruction, data_json, war_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (war_id) DO NOTHING
            """, (
                war_end_time_iso, war_summary['opponent_name'], war_summary['clan_stars'],
                war_summary['opponent_stars'], war_summary['clan_destruction'],
                df_json, war_date_formatted
            ))
        conn.commit()

# --- FUNÇÃO QUE ESTAVA FALTANDO ---
def is_war_saved(war_id):
    """Verifica se uma guerra com um ID específico já foi salva no banco."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # SELECT EXISTS é uma forma eficiente de checar se um registro existe
            cursor.execute("SELECT EXISTS(SELECT 1 FROM wars WHERE war_id = %s)", (war_id,))
            exists = cursor.fetchone()[0]
            return exists == 1

def get_war_history_list():
    """Retorna uma lista de todas as guerras salvas."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT war_id, opponent_name, war_date FROM wars ORDER BY war_date DESC")
            return cursor.fetchall()

def get_war_by_id(war_id):
    """Busca os dados de uma guerra específica."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM wars WHERE war_id = %s", (war_id,))
            war_data = cursor.fetchone()
            if war_data:
                df_attacks = pd.read_json(war_data[5], orient='split')
                summary = {
                    "opponent_name": war_data[1], "clan_stars": war_data[2],
                    "opponent_stars": war_data[3], "clan_destruction": war_data[4]
                }
                return summary, df_attacks
    return None, None

def get_top_war_performers(limit=5):
    """
    Busca as últimas guerras do histórico e calcula o ranking de performance.
    Compatível com dados antigos que não possuem todas as colunas.
    """
    war_data_rows = get_last_n_wars(limit=limit)
    if not war_data_rows:
        return pd.DataFrame()

    player_stats = defaultdict(lambda: {'Total Estrelas': 0, 'Total Destruição': 0, 'Total Duração': 0, 'Guerras': 0})
    
    for war_row in war_data_rows:
        df_war = pd.read_json(war_row[0], orient='split')
        for _, player_row in df_war.iterrows():
            if 'Nome' in player_row and 'Estrelas Totais' in player_row:
                player_name = player_row['Nome']
                player_stats[player_name]['Total Estrelas'] += player_row.get('Estrelas Totais', 0)
                player_stats[player_name]['Total Destruição'] += int(str(player_row.get('Destruição Total', '0%')).replace('%', ''))
                
                # --- CORREÇÃO APLICADA AQUI ---
                # Usamos .get(coluna, 0) para pegar o valor de forma segura.
                # Se a coluna 'Duração Total (s)' não existir, ele usa 0 e não dá erro.
                player_stats[player_name]['Total Duração'] += player_row.get('Duração Total (s)', 0)
                
                player_stats[player_name]['Guerras'] += 1
    
    if not player_stats:
        return pd.DataFrame()

    df_summary = pd.DataFrame.from_dict(player_stats, orient='index').reset_index().rename(columns={'index': 'Nome'})
    
    df_summary = df_summary.sort_values(
        by=['Total Estrelas', 'Total Destruição', 'Total Duração'],
        ascending=[False, False, True]
    )
    
    return df_summary.head(5)

