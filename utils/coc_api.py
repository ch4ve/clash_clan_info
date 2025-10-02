import streamlit as st
import pandas as pd
import coc
import asyncio
from collections import defaultdict

@st.cache_data(ttl="10m")
def get_clan_data(clan_tag, coc_email, coc_password):
    async def _fetch():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            clan = await client.get_clan(clan_tag)
            
            async def fetch_player_data(member):
                player = await client.get_player(member.tag)
                hero_levels = {h.name: h.level for h in player.heroes}
                return {
                    'Nome': player.name, 'Cargo': player.role.name, 'CV': player.town_hall,
                    'Liga': player.league.name if player.league else 'Sem Liga', 'Troféus': player.trophies,
                    'Rei Bárbaro': hero_levels.get('Barbarian King', 0), 'Rainha Arqueira': hero_levels.get('Archer Queen', 0),
                    'Grande Guardião': hero_levels.get('Grand Warden', 0), 'Campeã Real': hero_levels.get('Royal Champion', 0)
                }

            tasks = [fetch_player_data(member) for member in clan.members]
            members_data = await asyncio.gather(*tasks)

            return pd.DataFrame(members_data), clan.name
        finally:
            await client.close()
    return asyncio.run(_fetch())


@st.cache_data(ttl="5m")
def get_current_war_data(clan_tag, coc_email, coc_password):
    async def _fetch_war():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            try:
                war = await client.get_current_war(clan_tag)
            except coc.NotFound:
                return None, None, None, None, None
            opponent_map = {opponent.tag: opponent for opponent in war.opponent.members}
            attacks_data = []
            for member in war.clan.members:
                ataques_feitos = len(member.attacks)
                estrelas_atk1, cv_inimigo_atk1, destruicao_atk1, duracao_atk1 = 0, "-", 0, 0
                estrelas_atk2, cv_inimigo_atk2, destruicao_atk2, duracao_atk2 = 0, "-", 0, 0
                if ataques_feitos >= 1:
                    atk1 = member.attacks[0]
                    estrelas_atk1, destruicao_atk1, duracao_atk1 = atk1.stars, atk1.destruction, atk1.duration
                    inimigo1 = opponent_map.get(atk1.defender_tag)
                    if inimigo1: cv_inimigo_atk1 = inimigo1.town_hall
                if ataques_feitos == 2:
                    atk2 = member.attacks[1]
                    estrelas_atk2, destruicao_atk2, duracao_atk2 = atk2.stars, atk2.destruction, atk2.duration
                    inimigo2 = opponent_map.get(atk2.defender_tag)
                    if inimigo2: cv_inimigo_atk2 = inimigo2.town_hall
                attacks_data.append({'Posição': member.map_position, 'Nome': member.name, 'Ataques Feitos': ataques_feitos,'Estrelas Atk 1': estrelas_atk1, 'CV Inimigo Atk 1': cv_inimigo_atk1,'Estrelas Atk 2': estrelas_atk2, 'CV Inimigo Atk 2': cv_inimigo_atk2,'Destruição Atk 1': destruicao_atk1, 'Duração Atk 1 (s)': duracao_atk1,'Destruição Atk 2': destruicao_atk2, 'Duração Atk 2 (s)': duracao_atk2})
            df_attacks = pd.DataFrame(attacks_data)
            df_attacks['Estrelas Totais'] = df_attacks['Estrelas Atk 1'] + df_attacks['Estrelas Atk 2']
            df_attacks['Destruição Total'] = df_attacks['Destruição Atk 1'] + df_attacks['Destruição Atk 2']
            df_attacks['Duração Total (s)'] = df_attacks['Duração Atk 1 (s)'] + df_attacks['Duração Atk 2 (s)']
            df_display = df_attacks.copy()
            df_display['Destruição Total'] = df_display['Destruição Total'].apply(lambda x: f"{x}%")
            colunas_para_remover = ['Destruição Atk 1', 'Duração Atk 1 (s)', 'Destruição Atk 2', 'Duração Atk 2 (s)']
            df_display = df_display.drop(columns=colunas_para_remover)
            ordem_colunas_display = ['Posição', 'Nome', 'Ataques Feitos', 'Estrelas Totais', 'Estrelas Atk 1','CV Inimigo Atk 1', 'Estrelas Atk 2', 'CV Inimigo Atk 2','Destruição Total', 'Duração Total (s)']
            df_display = df_display[ordem_colunas_display]
            df_display = df_display.sort_values(by='Posição', ascending=True)
            war_summary = {"clan_name": war.clan.name, "opponent_name": war.opponent.name,"clan_stars": war.clan.stars, "opponent_stars": war.opponent.stars,"clan_destruction": war.clan.destruction, "opponent_destruction": war.opponent.destruction}
            return df_attacks, df_display, war_summary, war.state, war.end_time
        finally:
            await client.close()
    return asyncio.run(_fetch_war())

@st.cache_data(ttl="2h")
def get_cwl_data(clan_tag, coc_email, coc_password):
    async def _fetch_cwl():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            try:
                group = await client.get_league_group(clan_tag)
            except coc.NotFound:
                return None, None
            all_attacks_data = []
            war_day = 0
            async for war in group.get_wars_for_clan(clan_tag):
                war_day += 1
                clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
                for member in clan_side.members:
                    if member.attacks:
                        attack = member.attacks[0]
                        all_attacks_data.append({'Tag do Jogador': member.tag, 'Nome': member.name, 'Dia da Guerra': war_day, 'Estrelas': attack.stars})
            if not all_attacks_data:
                return pd.DataFrame(), group.season
            df_attacks = pd.DataFrame(all_attacks_data)
            summary = df_attacks.groupby(['Tag do Jogador', 'Nome']).agg(Total_Estrelas=('Estrelas', 'sum'), Ataques_Feitos=('Estrelas', 'size')).reset_index()
            summary['Media_Estrelas'] = (summary['Total_Estrelas'] / summary['Ataques_Feitos']).round(2)
            total_guerras_registradas = df_attacks['Dia da Guerra'].nunique()
            summary['Guerras_Ausente'] = total_guerras_registradas - summary['Ataques_Feitos']
            summary = summary.sort_values(by='Total_Estrelas', ascending=False)
            summary.rename(columns={'Nome': 'Nome do Jogador', 'Total_Estrelas': 'Total de Estrelas','Ataques_Feitos': 'Ataques Feitos', 'Media_Estrelas': 'Média de Estrelas','Guerras_Ausente': 'Guerras Ausente'}, inplace=True)
            return summary, group.season
        finally:
            await client.close()
    return asyncio.run(_fetch_cwl())

@st.cache_data(ttl="5m")
def get_cwl_current_war_details(clan_tag, coc_email, coc_password):
    async def _fetch_cwl_war():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            try:
                group = await client.get_league_group(clan_tag)
            except coc.NotFound:
                return None, None, None, None, None

            # --- LÓGICA CORRIGIDA ---
            # 1. Usamos o get_wars_for_clan() que sabemos que funciona
            async for war in group.get_wars_for_clan(clan_tag):
                # 2. Verificamos o estado da guerra manualmente
                if war.state == 'preparation' or war.state == 'inWar':
                    # Achamos a guerra do dia! Processa e retorna os dados.
                    clan_side = war.clan if war.clan.tag == clan_tag else war.opponent
                    opponent_side = war.opponent if war.clan.tag == clan_tag else war.clan

                    clan_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in clan_side.members]
                    df_clan = pd.DataFrame(clan_members_data).sort_values(by='Pos.')

                    opponent_members_data = [{'Pos.': m.map_position, 'Nome': m.name, 'CV': m.town_hall} for m in opponent_side.members]
                    df_opponent = pd.DataFrame(opponent_members_data).sort_values(by='Pos.')

                    war_summary = {
                        "opponent_name": opponent_side.name,
                        "state": war.state,
                        "start_time": war.start_time,
                        "end_time": war.end_time
                    }
                    return war_summary, df_clan, df_opponent, clan_side.tag, opponent_side.tag
            
            # 3. Se o loop terminar e não acharmos nenhuma guerra em preparação/andamento
            return None, None, None, None, None
        finally:
            await client.close()
            
    return asyncio.run(_fetch_cwl_war())
@st.cache_data(ttl="5m")
def get_scouting_report(our_clan_tag, coc_email, coc_password):
    async def _scout():
        df_schedule, _ = await asyncio.to_thread(get_cwl_schedule, our_clan_tag, coc_email, coc_password)
        if df_schedule is None or df_schedule.empty:
            return None, None, "Não foi possível carregar o cronograma."
        
        our_war_summary, df_our_clan, _, _, _ = await asyncio.to_thread(get_cwl_current_war_details, our_clan_tag, coc_email, coc_password)
        if our_war_summary is None:
            return None, None, "Não foi possível carregar nossa guerra atual."
        
        opponent_today = our_war_summary['opponent_name']
        try:
            current_day_row = df_schedule[df_schedule['Oponente'] == opponent_today]
            current_day = current_day_row['Dia'].iloc[0]
            next_day = current_day + 1
        except IndexError:
            return None, None, "Não foi possível determinar o dia da guerra atual no cronograma."
        if next_day > 7:
            return df_our_clan, None, "Último dia da liga, não há próximo oponente para espionar."
        
        next_opponent_row = df_schedule[df_schedule['Dia'] == next_day]
        if next_opponent_row.empty:
            return None, None, f"Não foi possível encontrar o oponente do Dia {next_day}."
        
        next_opponent_tag = next_opponent_row['Tag do Oponente'].iloc[0]
        next_opponent_name = next_opponent_row['Oponente'].iloc[0]

        _, their_clan_df, their_opponent_df, their_clan_tag, their_opponent_tag = await asyncio.to_thread(get_cwl_current_war_details, next_opponent_tag, coc_email, coc_password)
        
        if their_clan_df is None:
            return None, None, f"Não foi possível carregar a guerra atual de '{next_opponent_name}'."
        
        df_predicted_opponent = their_clan_df if their_clan_tag == next_opponent_tag else their_opponent_df

        return df_our_clan, df_predicted_opponent, next_opponent_name
    return asyncio.run(_scout())

@st.cache_data(ttl="6h")
def get_cwl_schedule(clan_tag, coc_email, coc_password):
    async def _fetch_schedule():
        client = coc.Client()
        try:
            await client.login(coc_email, coc_password)
            try:
                group = await client.get_league_group(clan_tag)
            except coc.NotFound:
                return None, None
            clan_map = {c.tag: c.name for c in group.clans}
            schedule = []
            for war_day, round_tags_list in enumerate(group.rounds, 1):
                our_war_tag = next((tag for tag in round_tags_list if clan_tag in tag), None)
                if our_war_tag:
                    tags = our_war_tag.replace("#", "").split("v")
                    opponent_tag = f"#{tags[1]}" if tags[0] == clan_tag.replace("#","") else f"#{tags[0]}"
                    schedule.append({'Dia': war_day, 'Oponente': clan_map.get(opponent_tag, "Desconhecido"), 'Tag do Oponente': opponent_tag})
            return pd.DataFrame(schedule), group.rounds
        finally:
            await client.close()
    return asyncio.run(_fetch_schedule())

