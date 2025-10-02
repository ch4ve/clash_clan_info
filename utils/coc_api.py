# NOVO CONTEÚDO COMPLETO para utils/coc_api.py

import pandas as pd
import coc
import asyncio
from collections import defaultdict
from .loop_manager import loop_manager # Importa nosso gerente

# --- FUNÇÕES SÍNCRONAS (WRAPPERS) ---
# O Streamlit chama estas funções. Elas simplesmente repassam o trabalho para o gerente.

def get_clan_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(
        _get_clan_data_async(clan_tag, coc_email, coc_password)
    )

def get_current_war_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(
        _get_current_war_data_async(clan_tag, coc_email, coc_password)
    )

def get_cwl_data(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(
        _get_cwl_data_async(clan_tag, coc_email, coc_password)
    )

def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(
        _get_cwl_current_war_details_async(clan_tag, coc_email, coc_password)
    )

def get_cwl_group_clans(clan_tag, coc_email, coc_password):
    return loop_manager.run_coroutine(
        _get_cwl_group_clans_async(clan_tag, coc_email, coc_password)
    )

def generate_full_league_preview(our_clan_tag, coc_email, coc_password):
    """Função síncrona que o Streamlit chama."""
    return loop_manager.run_coroutine(
        _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password)
    )


# ... (e assim por diante para todas as outras funções que você precisar)

# --- LÓGICA ASSÍNCRONA (CORE) ---
# As funções com "_" na frente contêm a lógica real e são chamadas pelo gerente.

async def _get_clan_data_async(clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)
        clan = await client.get_clan(clan_tag)
        
        async def fetch_player_data(member):
            player = await client.get_player(member.tag)
            hero_levels = {h.name: h.level for h in player.heroes}
            return {'Nome': player.name, 'Cargo': player.role.name, 'CV': player.town_hall, 'Liga': player.league.name if player.league else 'Sem Liga', 'Troféus': player.trophies, 'Rei Bárbaro': hero_levels.get('Barbarian King', 0), 'Rainha Arqueira': hero_levels.get('Archer Queen', 0), 'Grande Guardião': hero_levels.get('Grand Warden', 0), 'Campeã Real': hero_levels.get('Royal Champion', 0)}
        
        tasks = [fetch_player_data(member) for member in clan.members]
        members_data = await asyncio.gather(*tasks)
        return pd.DataFrame(members_data), clan.name
    finally:
        await client.close()

async def _get_current_war_data_async(clan_tag, coc_email, coc_password):
    # Cole aqui a lógica completa da sua função _get_current_war_data_async
    pass

async def _get_cwl_data_async(clan_tag, coc_email, coc_password):
    # Cole aqui a lógica completa da sua função _get_cwl_data_async
    pass

async def _get_cwl_current_war_details_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client:
            await client.login(coc_email, coc_password)
        
        group = await client.get_league_group(clan_tag)
        async for war in group.get_wars_for_clan(clan_tag):
            if war.state in ['preparation', 'inWar']:
                clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
                opponent_side = war.opponent if war.clan.tag == clan_tag else war.clan
                clan_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in clan_side.members]
                df_clan = pd.DataFrame(clan_members_data).sort_values(by='Pos.')
                opponent_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in opponent_side.members]
                df_opponent = pd.DataFrame(opponent_members_data).sort_values(by='Pos.')
                war_summary = {"clan_name": clan_side.name, "opponent_name": opponent_side.name, "state": war.state, "start_time": war.start_time, "end_time": war.end_time}
                return war_summary, df_clan, df_opponent, clan_side.tag, opponent_side.tag
        return None, None, None, None, None
    finally:
        if not existing_client:
            await client.close()

async def _get_scouting_report_async(our_clan_tag, coc_email, coc_password):
    client = coc.Client()
    try:
        await client.login(coc_email, coc_password)

        # Usando o cliente já logado para todas as chamadas
        our_war_summary, df_our_clan, _, _, _ = await _get_cwl_current_war_details_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if our_war_summary is None:
            return None, None, "Não foi possível carregar nossa guerra atual para determinar o dia."
        
        all_clans = await _get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password, existing_client=client)
        if not all_clans:
            return None, None, "Não foi possível carregar a lista de clãs do grupo."
            
        opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
        
        # Cria as tarefas de espionagem passando o cliente existente
        tasks = [_get_cwl_current_war_details_async(opponent.tag, coc_email, coc_password, existing_client=client) for opponent in opponents]
        scouting_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        league_preview = []
        for i, result in enumerate(scouting_results):
            opponent_name = opponents[i].name
            if isinstance(result, Exception) or result[0] is None:
                df_predicted_opponent = pd.DataFrame([{"Erro": "Não foi possível carregar a guerra deste clã."}])
            else:
                _, their_clan_df, their_opponent_df, their_clan_tag, _ = result
                df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            
            league_preview.append({'opponent_name': opponent_name, 'predicted_lineup': df_predicted_opponent})
            
        return df_our_clan, league_preview
    finally:
        await client.close()

async def _get_cwl_group_clans_async(clan_tag, coc_email, coc_password, existing_client=None):
    client = existing_client or coc.Client()
    try:
        if not existing_client:
            await client.login(coc_email, coc_password)
        group = await client.get_league_group(clan_tag)
        return group.clans
    finally:
        if not existing_client:
            await client.close()

# Adicione estas duas funções no final do seu arquivo utils/coc_api.py

async def _generate_full_league_preview_async(our_clan_tag, coc_email, coc_password):
    """Orquestra a coleta de dados para o mapa completo da liga."""
    
    # 1. Busca nossa própria escalação e a lista de todos os oponentes
    our_war_task = asyncio.create_task(_get_cwl_current_war_details_async(our_clan_tag, coc_email, coc_password))
    opponents_task = asyncio.create_task(_get_cwl_group_clans_async(our_clan_tag, coc_email, coc_password))

    our_war_summary, df_our_clan, _, _, _ = await our_war_task
    all_clans = await opponents_task

    if df_our_clan is None or all_clans is None:
        return None, None # Retorna se não conseguir pegar os dados iniciais
    
    opponents = [clan for clan in all_clans if clan.tag != our_clan_tag]
    
    # 2. Cria uma lista de "tarefas" para espionar cada oponente em paralelo
    scouting_tasks = []
    for opponent in opponents:
        scouting_tasks.append(_get_cwl_current_war_details_async(opponent.tag, coc_email, coc_password))
        
    # 3. Executa todas as tarefas de espionagem ao mesmo tempo (muito mais rápido!)
    scouting_results = await asyncio.gather(*scouting_tasks, return_exceptions=True)
    
    league_preview = []
    for i, result in enumerate(scouting_results):
        opponent_name = opponents[i].name
        
        # Verifica se a busca para este oponente deu erro
        if isinstance(result, Exception) or result[0] is None:
            df_predicted_opponent = pd.DataFrame([{"Erro": "Não foi possível carregar a guerra deste clã."}])
        else:
            # Extrai a escalação correta do oponente
            _, their_clan_df, their_opponent_df, their_clan_tag, _ = result
            df_predicted_opponent = their_clan_df if their_clan_tag == opponents[i].tag else their_opponent_df
            
        league_preview.append({
            'opponent_name': opponent_name,
            'predicted_lineup': df_predicted_opponent
        })
        
    return df_our_clan, league_preview



