import streamlit as st
import numpy as np
import pandas as pd
from mplsoccer import Pitch, VerticalPitch
from constants.const import *

shot_color_dict = {"Goal" : COMPLETED_COLOR,
                   "Blocked" : INJURY_CLEARANCE_COLOR,
                   "Off T" : INCOMPLETE_COLOR,
                   "Post" : POST_COLOR,
                   "Saved" : SAVED_COLOR,
                   "Wayward" : UNKNOWN_COLOR,
                   "Saved Off Target" : OUT_COLOR,
                   "Saved to Post" : SAVED_TO_POST_COLOR}

st.sidebar.title("Filter the Shot Data")
shot_filters = {}
body_part_filter = st.sidebar.multiselect("Select Body Part",
                                  ['Right Foot', 'Left Foot', 'Head', 'Keeper Arm', 'Other', 'Drop Kick'])
shot_filters['{}_body_part'.format("shot")] = body_part_filter
play_pattern_filter = st.sidebar.multiselect("Select Play Pattern",
                                     ['Regular Play', 'From Throw In', 'From Free Kick', 'From Goal Kick',
                                      'From Kick Off', 'From Keeper', 'From Corner', 'From Counter', 'Other'])
shot_filters['play_pattern'] = play_pattern_filter

type_filter = st.sidebar.multiselect("Select Play Type", ['Open Play', 'Free Kick', 'Penalty', 'Corner', 'Kick Off'])
technique_filter = st.sidebar.multiselect("Select Shot Technique",
                                  ['Normal', 'Volley', 'Half Volley', 'Backheel', 'Diving Header',
                                   'Lob', 'Overhead Kick'])
shot_filters['shot_type'] = type_filter
shot_filters['shot_technique'] = technique_filter


def shot_map(structured_shot_data, pitch):
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=True)
    pitch._draw_juego_de_posicion(ax)
    fig.set_facecolor(color=PITCH_COLOR)
    ax.patch.set_facecolor(color=PITCH_COLOR)
    for outcome, data in structured_shot_data.items():
        pitch.lines(data['start_x'], data['start_y'], data['end_x'], data['end_y'], color=shot_color_dict[outcome], ax=ax, lw=5,comet=True, label=outcome)
        ax.legend(facecolor=PITCH_COLOR, edgecolor=None, fontsize=20, loc='upper left')
    return fig, ax

def plot_shot_frame(shot_frame, shot, pitch):
    fig, ax = pitch.draw(figsize=(16, 10), constrained_layout=True, tight_layout=True)
    pitch._draw_juego_de_posicion(ax)
    fig.set_facecolor(color=PITCH_COLOR)
    ax.patch.set_facecolor(color=PITCH_COLOR)
    
    shot_frame["team"] = np.where(shot_frame["teammate"] == True, "Teammate", "Opposition")
    
    pitch.scatter(shot_frame[shot_frame["team"]=="Teammate"].x, shot_frame[shot_frame["team"]=="Teammate"].y, ax=ax, color="red", label="Teammate", marker="o")
    pitch.scatter(shot_frame[shot_frame["team"]=="Opposition"].x, shot_frame[shot_frame["team"]=="Opposition"].y, ax=ax, color="blue", label="Opposition", marker="<")
    pitch.scatter(shot['start_x'], shot['start_y'], shot['end_x'], ax=ax, color=COMPLETED_COLOR, label=selected_player)
    pitch.lines(shot['start_x'], shot['start_y'], shot['end_x'], shot['end_y'], color="gold", label=shot["shot_outcome"], ax=ax, lw=5,comet=True)
    
    ax.legend(facecolor=PITCH_COLOR, edgecolor=None, fontsize=20, loc='lower left')
    
    return fig, ax


@st.cache_data
def create_field(half=False):
    if half:
        field = VerticalPitch(half=half, pitch_color=PITCH_COLOR,line_color=LINE_COLOR, stripe_color=STRIPE_COLOR,stripe=True, pitch_type='statsbomb', positional=True,axis=True, pitch_width=120, pitch_length=80)    
    else:
        field = Pitch(half=half, pitch_color=PITCH_COLOR,line_color=LINE_COLOR, stripe_color=STRIPE_COLOR,stripe=True, pitch_type='statsbomb', positional=True,axis=True, pitch_width=120, pitch_length=80)

    return field

@st.cache_data
def prepare_data_for_plotting(events, outcomes):
    event_type = "shot"
    all_coordinates = []
    outcome_data = {}
    for outcome in sorted(outcomes, reverse=True):
        period_events = events.where(events['{}_outcome'.format(event_type)] == outcome).reset_index(drop=True)

        start_pos = period_events.location.values.tolist()
        start_pos = pd.DataFrame(data=[str(pos).strip("""[]""").split(',')[:2] for pos in start_pos],
                                 columns=['start_x', 'start_y'])
        start_pos = start_pos.astype({"start_x": float, "start_y": float})

        end_pos = period_events['{}_end_location'.format(event_type)].values.tolist()
        end_pos = pd.DataFrame(data=[str(pos).strip("""[]""").split(',')[:2] for pos in end_pos],
                               columns=['end_x', 'end_y'])
        end_pos = end_pos.astype({"end_x": float, "end_y": float})

        coordinates = pd.concat([start_pos, end_pos, period_events['{}_outcome'.format(event_type)]],
                                axis=1)
        outcome_data[outcome] = coordinates
        all_coordinates.append(coordinates)

    every_event = pd.concat(all_coordinates)
    return every_event.dropna().sort_values(by=["shot_outcome"]).reset_index(drop=True), outcome_data

@st.cache_data
def get_shot_frames(events):
    raw_frames = events["shot_freeze_frame"].values.tolist()
    shot_frames = []
    for frame in raw_frames:
        try:
            shot_frame = []
            for player in frame:
                position = player["location"]
                teammate = player["teammate"]
                shot_frame.append(pd.DataFrame(data={"x" : [position[0]], "y" : [position[1]], "teammate" : [teammate]}))
            shot_frames.append(pd.concat(shot_frame))
        except TypeError:
            shot_frames.append(pd.DataFrame(data=[], columns=["x", "y", "teammate"]))
    return shot_frames



@st.cache_data
def get_shot_stats(events):
    extra_columns = ['location', "duration", 'position', "period", "under_pressure", 'play_pattern', 'period']
    player_events = events[events['type'] == "Shot"]
    event_type_columns = [str(column) for column in player_events.columns.values.tolist() if "shot" in column] + extra_columns
    shot_events = player_events[event_type_columns].sort_values(by=["shot_outcome"]).reset_index(drop=True)
    return shot_events


@st.cache_data
def get_outcomes(player_events):
    selected_type = "Shot"
    absolute_outcomes = player_events[["{}_outcome".format(selected_type.lower())]].value_counts(ascending=True,
                        dropna=False).to_frame("Count")
    return absolute_outcomes

@st.cache_data
def showcase_shotdataframe(shots_stats):
    
    shots = shots_stats[["shot_technique", "shot_body_part", "shot_outcome", "shot_statsbomb_xg"]].rename(columns = {"shot_technique" : "Technique", 
                                   "shot_body_part" : "Body part", 
                                   "shot_statsbomb_xg" : "xG", 
                                   "shot_outcome" : "Outcome"}
                                   )
     
    return shots


@st.cache_data
def filter_stats(player_events, conditions):
    filtered_events = player_events
    for key in conditions:
        if not conditions[key]:
            continue
        else:
            filtered_events = filtered_events.query("{} in {}".format(key, conditions[key]))
    return filtered_events.sort_values(by="shot_outcome").reset_index(drop=True)


if st.session_state["selected_player"] != SELECTBOX_DEFAULT:


    selected_player = st.session_state["selected_player"]
    player_stats = st.session_state["player_stats"]

    shot_stats = get_shot_stats(player_stats)
    shot_stats = filter_stats(shot_stats, shot_filters)
    if len(shot_stats.index) > 0:

        st.markdown("<h1 style='text-align: center; color: black;'>Shooting Stats of {}</h1>".format(selected_player), unsafe_allow_html=True)
       
        outcomes = get_outcomes(shot_stats)

        outcome_names_original = [outcome[0].strip("""()',""") for outcome in outcomes.index]

        plot_data, structured_plot_data = prepare_data_for_plotting(shot_stats, outcome_names_original)
        shot_df = showcase_shotdataframe(shot_stats)

        shot_frames = get_shot_frames(shot_stats)
        shot_frame_indexes = shot_df.index.values.tolist()

        shot_frame_names = (shot_df["Outcome"] + " Shot with "  + round(shot_df["xG"], 2).astype(str) + " of xG").values.tolist() 
        frame_per_id = {}
        for (frame, index) in zip(shot_frame_names, shot_frame_indexes):
            frame_per_id[frame] = index

        with st.expander("Shooting Stats", expanded=True):
            shot_amount, goals, xg = st.columns(3)
            with shot_amount:
                if len(shot_df.index) > 0:
                    st.metric("Shots", value=len(shot_df.index))    
            with xg:
                if len(shot_df["xG"].notna())>0:
                    st.metric("Cumulative xG", value=round(shot_df["xG"].sum(),2))
            with goals:
                if len(shot_df[shot_df["Outcome"]=="Goal"])>0:
                    st.metric("Goal(s)", value=shot_df[shot_df["Outcome"]=="Goal"]["Outcome"].count())
        
            st.dataframe(shot_df, width=1000)


        field_original = create_field()

        field_original, ax_originial = shot_map(structured_plot_data, field_original)
        st.pyplot(field_original)

        with st.expander("Shot Freeze Frames", expanded=False):
            selected_frame = st.selectbox("Select Shot Frame:", shot_frame_names)
            if selected_frame != SELECTBOX_DEFAULT:
                selected_frame_index = frame_per_id[selected_frame]
                field_shot_frame, ax_shot_frame = plot_shot_frame(shot_frames[selected_frame_index], plot_data.iloc[selected_frame_index], create_field(half=True))
                st.pyplot(field_shot_frame)

    else:
        st.write("No Shots to show with the selected parameters for {} :(".format(st.session_state["selected_player"]))





