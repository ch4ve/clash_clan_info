# Conteúdo CORRIGIDO e COMPLETO de utils/database.py

import sqlite3
import pandas as pd  # <<<--- ESTA É A LINHA QUE FALTAVA
import json
from collections import defaultdict

DB_FILE = "clash_history.db"

def init_db():
    """Cria o banco de dados e garante que a tabela 'wars' tenha a estrutura mais recente."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wars (
                war_id TEXT PRIMARY KEY,
                opponent_name TEXT NOT NULL,
                clan_stars INTEGER,
                opponent_stars INTEGER,
                clan_destruction REAL,
                data_json TEXT NOT NULL,
                war_date TEXT
            )
        """)
        try:
            cursor.execute("ALTER TABLE wars ADD COLUMN war_date TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()

def save_war_data(war_summary, df_attacks, war_end_time_iso):
    """Salva os dados de uma guerra no banco de dados, incluindo a data formatada."""
    df_json = df_attacks.to_json(orient='split')
    war_date_formatted = war_end_time_iso.split('T')[0]
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO wars (war_id, opponent_name, clan_stars, opponent_stars, clan_destruction, data_json, war_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            war_end_time_iso,
            war_summary['opponent_name'],
            war_summary['clan_stars'],
            war_summary['opponent_stars'],
            war_summary['clan_destruction'],
            df_json,
            war_date_formatted
        ))
        conn.commit()

def get_war_history_list():
    """Retorna uma lista de todas as guerras salvas para usar no filtro."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT war_id, opponent_name, war_date FROM wars ORDER BY war_id DESC")
        return cursor.fetchall()

def get_war_by_id(war_id):
    """Busca os dados de uma guerra específica pelo seu ID."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wars WHERE war_id = ?", (war_id,))
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
    Busca as últimas 'limit' guerras do histórico, calcula o desempenho
    agregado de cada jogador e retorna o ranking dos 5 melhores.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM wars ORDER BY war_date DESC LIMIT ?", (limit,))
        war_data = cursor.fetchall()
        
        if not war_data:
            return pd.DataFrame()

        player_stats = defaultdict(lambda: {'Total Estrelas': 0, 'Total Destruição': 0, 'Total Duração': 0})
        
        for war_row in war_data:
            df_war = pd.read_json(war_row[0], orient='split')
            for _, player_row in df_war.iterrows():
                player_name = player_row['Nome']
                player_stats[player_name]['Total Estrelas'] += player_row['Estrelas Totais']
                player_stats[player_name]['Total Destruição'] += int(str(player_row['Destruição Total']).replace('%', ''))
                player_stats[player_name]['Total Duração'] += player_row['Duração Total (s)']
        
        if not player_stats:
            return pd.DataFrame()

        df_summary = pd.DataFrame.from_dict(player_stats, orient='index')
        df_summary.reset_index(inplace=True)
        df_summary.rename(columns={'index': 'Nome'}, inplace=True)

        df_summary = df_summary.sort_values(
            by=['Total Estrelas', 'Total Destruição', 'Total Duração'],
            ascending=[False, False, True]
        )
        
        return df_summary.head(5)
