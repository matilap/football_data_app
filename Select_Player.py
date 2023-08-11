import streamlit as st
import pandas as pd
from statsbombpy import sb
from constants.const import SELECTBOX_DEFAULT
import itertools


def clear_states():
    st.session_state["selected_competition"] = SELECTBOX_DEFAULT
    st.session_state["selected_season"] = SELECTBOX_DEFAULT
    st.session_state["selected_teams"] = SELECTBOX_DEFAULT
    st.session_state["selceted_matches"] = SELECTBOX_DEFAULT
    st.session_state["player_stats"] = SELECTBOX_DEFAULT
    st.session_state["selected_player"] = SELECTBOX_DEFAULT


def clear_state(state):
    st.session_state[state] = SELECTBOX_DEFAULT


if "selected_competition" not in st.session_state:
    clear_state("selected_competition")
if "selected_season" not in st.session_state:
    clear_state("selected_season")
if "selected_teams" not in st.session_state:
    clear_state("selected_teams")
if "selected_player" not in st.session_state:
    clear_state("selected_player")
if "player_stats" not in st.session_state:
    clear_state("player_stats")
if "selected_matches" not in st.session_state:
    clear_state("selected_matches")


st.title("Statsbombpy Data Visualisation App")

st.sidebar.header("Parameters For Visualisation")

comp = sb.competitions()
comp = comp[['competition_id','season_id', 'competition_name', 'season_name', 'competition_gender']]

comp_names = [str(competition).strip("""[ ] ' ' """) for competition in comp[['competition_name']].drop_duplicates().where(comp.competition_gender=='male').dropna().values.tolist()]
selected_comp = st.sidebar.selectbox("Select Competition:", comp_names, on_change=clear_states())
    

st.session_state["selected_competition"] = selected_comp

season_holder = comp.where(comp.competition_name==str(selected_comp)).dropna()[['competition_id','season_id', 'season_name']]
seasons = season_holder[['season_name']].values.tolist()
seasons = [str(season).strip("""[ ] ' ' \ """) for season in seasons]


selected_season = st.sidebar.selectbox("Select Season:", seasons, on_change=clear_states())

st.session_state["selected_season"] = selected_season
selected_comp_id, selected_season_id = season_holder.where(season_holder.season_name == """{}""".format(selected_season)).dropna().values.tolist()[0][:2]
selected_comp_id, selected_season_id = int(selected_comp_id), int(selected_season_id)


@st.cache_data
def get_match_ids(matches, indexes):
    match_ids = matches[['match_id']]
    ids = []
    for index, match_id in match_ids.iterrows():
        if index in indexes:
            ids.append(int(match_id[0]))
    return ids

@st.cache_data(show_spinner=False)
def get_players_of_team(match_id, team_names):
    match_id = int(str(match_id).strip("""[ ] ' ' """))
    team_names = [str(team_name).strip("""[ ]  " " ' ' """) for team_name in team_names]
    players = []
    all_events = sb.events(match_id=match_id)
    team_and_player = all_events[['team', 'player']]
    team_events = team_and_player[team_and_player['team'].isin(team_names)].dropna().drop_duplicates()
    all_players = [str(player).strip(""" [ ] " "  ' ' """) for player in team_events[['player']].values.tolist()]
    for player in all_players:
        if player not in players:
            players.append("""{}""".format(player))
    return players


@st.cache_data
def showcase_selections(indexes, matches):
    st.subheader("""Selected Matches""")
    st.dataframe(matches[matches.index.isin(indexes)].rename(columns={'home_team': 'Home', 'away_team': 'Away', 'score': 'Result'})[['Home', 'Away', 'Result']], use_container_width=True)

    ids = get_match_ids(matches, selected_indexes)

    return ids

@st.cache_data
def get_stats(match_id, player_name):
    events = sb.events(match_id=int(match_id))
    player_events = events[(events['player'] == player_name)]
    return player_events

matches = sb.matches(competition_id=selected_comp_id, season_id=selected_season_id)[['match_id','home_team', 'away_team', 'home_score', 'away_score']]
matches['score'] = matches.home_score.astype(str) + ' - ' + matches.away_score.astype(str)

teams = matches[['home_team']].drop_duplicates().values.tolist()
teams_away = matches[['away_team']].drop_duplicates().values.tolist()

for team in teams_away:
    if team not in teams:
        teams.append(team)

teams = [str(team).strip("""[ ] ' ' """) for team in teams]

selected_team = st.sidebar.multiselect("Select Team(s):", sorted(teams), on_change=clear_state("selected_matches"))
st.session_state["selected_team"] = selected_team


st.subheader("""All The Matches In Selected Season""")

matches_df = st.dataframe(matches.rename(columns={'home_team' : 'Home', 'away_team' : 'Away','score' : 'Result'})[
            ['Home', 'Away', 'Result']][matches.home_team.isin(selected_team) | matches.away_team.isin(selected_team)], use_container_width=True)
match_container = st.container()
select_all = st.checkbox('Select all available matches')

selectable_matches = matches[matches.home_team.isin(selected_team) | matches.away_team.isin(selected_team)]

match_options = (selectable_matches.home_team.astype(str) + " vs. " + selectable_matches.away_team.astype(str) + " "  + selectable_matches.score).values.tolist()
option_indexes = selectable_matches.index.values.tolist()
options = {}
for match, index in zip(match_options, option_indexes):
    options[match] = index

if select_all:
    selected_matches = match_container.multiselect('Select Matches:', match_options, default=match_options)
    selected_indexes = [options[match] for match in selected_matches]
    
else:
    selected_matches = match_container.multiselect('Select Matches:', match_options)
    selected_indexes = [options[match] for match in selected_matches]

if selected_indexes != []:
    match_ids = showcase_selections(selected_indexes, matches)
   
    with st.spinner("Searching the players"):
        selectable_players =  [get_players_of_team(match_id, selected_team) for match_id in match_ids]
        selectable_players = list(set(itertools.chain.from_iterable(selectable_players)))
        

    selectable_players.insert(0, SELECTBOX_DEFAULT)
    selected_player = st.selectbox('Select Player', selectable_players)

    if selected_player != SELECTBOX_DEFAULT:
        
        with st.spinner("Searching the stats"):
            player_stats = [sb.events(match_id=int(match_id))[sb.events(match_id=int(match_id))['player'] == selected_player] for match_id in match_ids]
            player_stats = pd.concat(player_stats, axis=0)
            st.session_state["selected_player"] = selected_player
            st.session_state["player_stats"] = player_stats
            st.session_state["selected_matches"] = selected_indexes
            st.write("Stats searched succesfully. Navigate to Pass and Shots pages.")










