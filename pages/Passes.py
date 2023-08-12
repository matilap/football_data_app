import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
import seaborn as sns
from constants.const import *


pass_color_dict = {"Complete" : COMPLETED_COLOR,
                   "Incomplete": INCOMPLETE_COLOR,
                   "Injury Clearance" : INJURY_CLEARANCE_COLOR,
                   "Out" : OUT_COLOR,
                   "Pass Offside" : PASS_OFFSIDE_COLOR,
                   "Unknown" : UNKNOWN_COLOR,
                   "Goal Assist" : GOAL_ASSIST_COLOR,
                   "Shot Assist" : SHOT_ASSIST_COLOR
                   }





st.sidebar.title("Filter the Pass Data")
pass_filters = {}

pass_outcome_filter = st.sidebar.multiselect("Select Wanted Outcome", ["Complete", "Incomplete", "Injury Clearence", "Out", "Pass Offside", "Unknown", "Shot Assist", "Goal Assist"])

body_part_filter = st.sidebar.multiselect("Select Body Part",
                                          ['Right Foot', 'Left Foot', 'Head', 'Keeper Arm', 'Other', 'Drop Kick'])
pass_filters['{}_body_part'.format("pass")] = body_part_filter

type_filter = st.sidebar.multiselect("Select Play Type", ['Recovery', 'Free Kick', 'Throw-in', 'Goal Kick', 'Interception',
                                                      'Kick Off', 'Corner'])
technique_filter = st.sidebar.multiselect("Select Pass Technique",
                                  ['Normal', 'Volley', 'Half Volley', 'Backheel', 'Diving Header', 'Lob',
                                   'Overhead Kick'])
pass_height_filter = st.sidebar.multiselect("Select Pass Height", ['Ground Pass', 'Low Pass', 'High Pass'])
pass_length_filter = st.sidebar.slider("Select Pass Range (in Meters)", 0, int(180 / 1.0936), (0, int(180 / 1.0936)))

pass_filters['pass_type'] = type_filter
pass_filters['pass_technique'] = technique_filter
pass_filters['pass_height'] = pass_height_filter
pass_filters['pass_length'] = pass_length_filter
pass_filters["pass_outcome"] = pass_outcome_filter


@st.cache_data
def create_field():
    field = Pitch(pitch_color=PITCH_COLOR, line_color=LINE_COLOR, stripe_color=STRIPE_COLOR,stripe=True, pitch_type='statsbomb', positional=True,axis=True, pitch_width=120, pitch_length=80)

    return field

@st.cache_data
def prepare_data_for_plotting(events, outcomes):
    all_coordinates = []
    outcome_data = {}
    for outcome in sorted(outcomes, reverse=True):
        period_events = events.where(events["pass_outcome"] == outcome).reset_index(drop=True)
        start_pos = period_events.location.values.tolist()
        start_pos = pd.DataFrame(data=[str(pos).strip("""[]""").split(',')[:2] for pos in start_pos],
                                 columns=['start_x', 'start_y'])
        start_pos = start_pos.astype({"start_x": float, "start_y": float})

        end_pos = period_events['pass_end_location'].values.tolist()
        end_pos = pd.DataFrame(data=[str(pos).strip("""[]""").split(',')[:2] for pos in end_pos],
                               columns=['end_x', 'end_y'])
        end_pos = end_pos.astype({"end_x": float, "end_y": float})
        coordinate_columns = [start_pos, end_pos]
        try:
            coordinate_columns.append(period_events["pass_outcome"])
            coordinates = pd.concat(coordinate_columns,
                                axis=1).dropna().reset_index(drop=True)
            outcome_data[outcome] = coordinates
            all_coordinates.append(coordinates)
        except:
            pass
    try:
        every_event = pd.concat(all_coordinates)
    except:
        every_event = 0
    return every_event, outcome_data


@st.cache_data
def get_pass_stats(events):
    extra_columns = ['location', "duration", 'position', "period", "under_pressure", 'play_pattern']
    player_events = events[events['type'] == "Pass"]
    event_type_columns = [str(column) for column in player_events.columns.values.tolist() if "pass" in column] + extra_columns
    pass_events = player_events[event_type_columns].reset_index(drop=True)
    try:
        shot_assists = pass_events[(pass_events.pass_shot_assist == True)].reset_index(drop=True)
        goal_assists = pass_events[(pass_events.pass_goal_assist == True)].reset_index(drop=True)
        pass_events = pass_events.where(pass_events.pass_shot_assist.isna() & pass_events.pass_goal_assist.isna()).reset_index(drop=True)
        if len(shot_assists.index) > 0:
            shot_assists["pass_outcome"] = "Shot Assist"
            #pass_events = pass_events.append(shot_assists, ignore_index=True).reset_index(drop=True)
            pass_events = pd.concat([pass_events, shot_assists]).reset_index(drop=True)
        if len(goal_assists.index) > 0:
            goal_assists["pass_outcome"] = "Goal Assist"
            #pass_events = pass_events.append(goal_assists, ignore_index=True).reset_index(drop=True)
            pass_events = pd.concat([pass_events, goal_assists]).reset_index(drop=True)
    except AttributeError:
        pass

    return pass_events


@st.cache_data
def showcase_dataframe(player_events):
    selected_type = "Pass"
    abs_outcomes = player_events[["{}_outcome".format(selected_type.lower())]].value_counts(ascending=True,
                                                                                         dropna=False).to_frame("Count")
    rel_outcomes = abs_outcomes.join(
        player_events[["{}_outcome".format(selected_type.lower())]].value_counts(ascending=True, normalize=True).mul(
            100).round(1).to_frame("Percentage [%]"))

    total_outcome_df = pd.DataFrame([rel_outcomes.sum(axis=0)], columns=rel_outcomes.columns)
    try:
        outcome_distribution_df = pd.concat([rel_outcomes.reset_index(), total_outcome_df.reset_index()], axis=0)
        outcome_distribution_df = outcome_distribution_df.rename(
        columns={"{}_outcome".format(selected_type.lower()): "{} Outcome".format(selected_type)})[
        ["{} Outcome".format(selected_type), 'Count', 'Percentage [%]']].replace({"""{} Outcome""".format(selected_type): np.nan}, "Total")
    except:
        outcome_distribution_df = 0

    return outcome_distribution_df, abs_outcomes, rel_outcomes

@st.cache_data
def filter_stats(player_events, conditions):
    filtered_events = player_events
    for key in conditions:
        if not conditions[key]:
            continue
        elif key == 'pass_length':
            val_range = str(conditions[key]).strip('( )')
            min_value = val_range.split(',')[0]
            max_value = val_range.split(',')[1]
            filtered_events = filtered_events.query("""{}>={} & {}<={}""".format(key, float(min_value) * 1.0936, key, float(max_value) * 1.0936))
        else:
            filtered_events = filtered_events.query("{} in {}".format(key, conditions[key]))
    return filtered_events


def heat_map(every_pass, field, ax, pitch):
        try:
            pitch.kdeplot(x=every_pass['start_x'], y=every_pass['start_y'], ax=ax,
                        fill=True,
                        cmap='light:b',
                        n_levels=5,
                        alpha=.5,
            )
        except:
            pass
        return field, ax

def pass_map(structured_pass_data, pitch):
    fig, ax = pitch.draw(figsize=(16, 11), constrained_layout=True, tight_layout=True)
    pitch._draw_juego_de_posicion(ax)
    fig.set_facecolor(color='white')
    ax.patch.set_facecolor(color=PITCH_COLOR)
    for outcome, data in structured_pass_data.items():
        pitch.lines(data['start_x'], data['start_y'], data['end_x'], data['end_y'], color=pass_color_dict[outcome],
                        ax=ax, lw=5, comet=True, label=outcome)

    ax.legend(facecolor=PITCH_COLOR, edgecolor=None, fontsize=20, loc='upper left')
    return fig, ax, pitch


if st.session_state["selected_player"] != SELECTBOX_DEFAULT:

    selected_player = st.session_state["selected_player"]
    player_stats = st.session_state["player_stats"]

    pass_stats = get_pass_stats(player_stats)
    pass_stats = pass_stats.replace({"pass_outcome": np.nan}, "Complete")
    pass_stats = filter_stats(pass_stats, pass_filters)
    if len(pass_stats.index) > 0:
        st.markdown("<h1 style='text-align: center; color: black;'>Passing Stats of {}</h1>".format(selected_player), unsafe_allow_html=True)
        original_outcome_distribution_df, original_absolute_outcomes, original_relative_outcomes = showcase_dataframe(pass_stats)
        outcome_names_original = [outcome[0].strip("""()',""") for outcome in original_relative_outcomes.index]
        plot_data, structured_plot_data = prepare_data_for_plotting(pass_stats, outcome_names_original)

        kpi, bar_chart = st.columns(2)

        with kpi:
            try:
                pass_eff = 0
                if "Complete" in outcome_names_original:
                    pass_eff += original_outcome_distribution_df.loc[original_outcome_distribution_df["Pass Outcome"]=="Complete"].values.tolist()[-1][-1]
                if "Shot Assist" in outcome_names_original:
                    pass_eff += original_outcome_distribution_df.loc[original_outcome_distribution_df["Pass Outcome"]=="Shot Assist"].values.tolist()[-1][-1]
                if "Goal Assist" in outcome_names_original:
                    pass_eff += original_outcome_distribution_df.loc[original_outcome_distribution_df["Pass Outcome"]=="Goal Assist"].values.tolist()[-1][-1]

                if pass_eff != 0 or pass_eff != np.nan:
                    st.metric(label="Passing Efficiency", value="{}%".format(round(pass_eff, 1)))
                else:
                   pass
                st.metric(label="Average Pass length", value="{} m".format(round(pass_stats.pass_length.mean(),1)))
                most_passes_with = pass_stats.pass_recipient.dropna().value_counts().to_frame().head(1).index[0]
                st.metric(label="Most Passes ({}) with".format(
                    str(pass_stats.pass_recipient.dropna().value_counts().to_frame().head(1).values[0]).strip('[]')),
                      value="{}".format(most_passes_with))

            except IndexError:
                pass
            try:
                st.metric(label="Goal Assists", value=str(pass_stats.pass_goal_assist.value_counts().to_frame().values.tolist()[0]).strip("""[]"""))
            except IndexError:
                pass
    
        with bar_chart:
            pass_fig, pass_ax = plt.subplots(1, 1, figsize=(20, 20))
            sns.set_theme(palette="light:b")

            plt.bar(outcome_names_original, original_absolute_outcomes["Count"].values, color="b")

            st.bar_chart(
                original_outcome_distribution_df[:-1].rename(columns={"Count": "Passes"}).set_index("Pass Outcome")[
                    "Passes"],
                use_container_width=True,
            )




        with st.expander("Field", expanded=False):
            pass_map_column, heatmap_column = st.columns(2)
            field_orig = create_field()
            with pass_map_column:
                pass_map_box = st.checkbox("Pass Map", value=False)
                if pass_map_box:
                    with heatmap_column:
                        field_orig, ax_orig, pitch = pass_map(structured_plot_data, field_orig)
                        heatmap_box = st.checkbox("Pass Position Heatmap", value=False)
                        if heatmap_box:
                            field_orig, ax_orig = heat_map(plot_data, field_orig, ax_orig, pitch)
                else:
                    with heatmap_column:
                        heatmap_box = st.checkbox("Pass Position Heatmap", value=False)
                        if heatmap_box:
                            pitch = field_orig
                            field_orig, ax_orig = pitch.draw()
                            field_orig, ax_orig = heat_map(plot_data, field_orig, ax_orig, pitch)
            if pass_map_box:
                st.pyplot(field_orig)
            elif heatmap_box:
                st.pyplot(field_orig)
            else:
                st.pyplot(field_orig.draw()[0])

        with st.expander("Datatable", expanded=False):

            st.dataframe(original_outcome_distribution_df, use_container_width=True)


        with st.expander("Length Distribution", expanded=False):
            nbins = st.slider("Select amount of bins", 1, 25, 10)
            fig, ax = plt.subplots()
            ax.hist(pass_stats.pass_length, bins=nbins, color="b", histtype="stepfilled")
            ax.set_title("Pass Length Distribution")
            st.pyplot(fig)
    else:
        st.write("No Passes to show with the selected parameters for {} :(".format(st.session_state["selected_player"]))
