# Statsbombpy Data Visualisation App

This is a Streamlit web application that utilizes the Statsbombpy library to visualise free football match data on a player level. Have a look at it from [here](https://footballdataapp-hb9zf2sbzykarytrgkc3qp.streamlit.app/).

## Features

- Select competitions and seasons.
- Choose teams to view matches in the selected season involving those teams.
- Display match details such as home and away teams, and scores.
- Select specific matches to view detailed statistics for individual players.
- Display player-specific pass and shot event statistics for the selected matches



## About the app

All the event data visualisations are done with mplsoccer https://mplsoccer.readthedocs.io/en/latest/. Also, check out the Statsbomb's free API documentation from here https://github.com/statsbomb/statsbombpy

As with every app, this comes also with couple of downsides:
- Streamlit supports concurrency poorly
- Streamlit disables reading the session states from an external file --> This leads to the main page clearing out the selected parameters which is annoying

  
  


