# Conteúdo de utils/database.py (com a nova coluna de data)

import sqlite3
import pandas as pd
import json

DB_FILE = "clash_history.db"

def init_db():
    """Cria o banco de dados e garante que a tabela 'wars' tenha a estrutura mais recente."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 1. Cria a tabela se ela não existir, já com a nova coluna
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wars (
                war_id TEXT PRIMARY KEY,
                opponent_name TEXT NOT NULL,
                clan_stars INTEGER,
                opponent_stars INTEGER,
                clan_destruction REAL,
                data_json TEXT NOT NULL,
                war_date TEXT  -- <<< NOVA COLUNA ADICIONADA
            )
        """)
        
        # 2. Lógica de "migração": Adiciona a coluna se a tabela já existia mas não tinha a coluna
        # Isso garante que o código não quebre se você já tiver um banco de dados antigo.
        try:
            cursor.execute("ALTER TABLE wars ADD COLUMN war_date TEXT")
        except sqlite3.OperationalError:
            # A coluna provavelmente já existe, o que é esperado.
            pass
            
        conn.commit()

def save_war_data(war_summary, df_attacks, war_end_time_iso):
    """Salva os dados de uma guerra no banco de dados, incluindo a data formatada."""
    df_json = df_attacks.to_json(orient='split')
    # Extrai a data (yyyy-mm-dd) do timestamp completo
    war_date_formatted = war_end_time_iso.split('T')[0]
    
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 3. Atualiza o comando INSERT para incluir o valor na nova coluna
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
            war_date_formatted # <-- Novo valor sendo salvo
        ))
        conn.commit()

def get_war_history_list():
    """Retorna uma lista de todas as guerras salvas para usar no filtro."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 4. Busca a nova coluna para usar na formatação do filtro
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