# -*- coding: utf-8 -*-
"""
Created on Tue Jun  4 22:45:04 2024

@author: Erdem Emin Akcay
"""

import re
import pandas as pd
import time
import plotly.graph_objects as go

#Read CSV file which different information gathered from web
all_assists_df = pd.read_csv('galatasaray_assists.csv')

# New column indicating "Home" or "Away" based on starting word in "match_name"
all_assists_df["team"] = all_assists_df["match_name"].str.split().str[0].apply(lambda x: "Home" if x == "Galatasaray" else "Away")

# remove goals from penalties
filtered_df = all_assists_df[~all_assists_df['assists'].str.contains("(pen.)")]

# remove own goals
filtered_df = filtered_df[~filtered_df['assists'].str.contains("(k.k)")]

# remove goals without assists
filtered_df = filtered_df[filtered_df['assists'].str.count('\(') + filtered_df['assists'].str.count('\)') >= 4]

def extract_name(text):
  """Extracts the text between the first opening and closing parentheses.

  Args:
      text: The string to extract the text from.

  Returns:
      The extracted text or None if no parentheses are found.
  """
  if pd.isna(text):
    return None
  opening_bracket = text.find('(')
  closing_bracket = text.find(')')
  if opening_bracket != -1 and closing_bracket > opening_bracket:
    return text[opening_bracket+1:closing_bracket]
  else:
    return None

def extract_before_bracket(text):
  """Extracts the text between the last closing bracket and the opening bracket before that.

  Args:
      text: The string to extract the text from.

  Returns:
      The extracted text or None if no parentheses are found.
  """
  if pd.isna(text):
    return None
  last_closing_bracket = text.rfind(')')
  first_opening_bracket = text.rfind('(', 0, last_closing_bracket)
  if last_closing_bracket != -1 and first_opening_bracket < last_closing_bracket:
    return text[first_opening_bracket+1:last_closing_bracket]
  else:
    return None

#If Galatasaray is the Home team we can get the assist maker by extract_name function
filtered_home = filtered_df[filtered_df['team'] == 'Home']

filtered_home['player_name'] = filtered_home['assists'].apply(extract_name)

#If Galataray is the Away team we can get the assist maker by the extract_before_bracket function
filtered_awway = filtered_df[filtered_df['team'] == 'Away']

filtered_awway['player_name'] = filtered_awway['assists'].apply(extract_before_bracket)    

#combine datasets back
combined_df = pd.concat([filtered_home, filtered_awway], ignore_index=True)

#remove if we end up player names like 1-0, this indicates that these are the goals by
#opposition teams
combined_df = combined_df[~combined_df['player_name'].str.contains('\d')]        

def extract_goal(assists, player_name):
  """Extracts the goal scorer name from the assists column after removing the player_name.

  Args:
      assists: The string containing assist information.
      player_name: The player name to remove from the assists string.

  Returns:
      The extracted goal scorer name, or None if not found.
  """
  if pd.isna(assists) or pd.isna(player_name):
    return None
  player_name_removed = assists.replace(player_name, '')  
  return re.sub(r'[\d]', '',re.sub(r'[^\w\s]', '', player_name_removed)).strip()  


#get goal scorer by extract_goal function
combined_df['goal_scorer'] = combined_df.apply(lambda row: extract_goal(row['assists'], row['player_name']), axis=1)       

#count how many times players assisted each other                           
assists_to_goals = combined_df.groupby(['player_name', 'goal_scorer']).size().reset_index(name='count')                           

#prepare data for Sankey graph
assist_makers = assists_to_goals['player_name']
goal_scorers = assists_to_goals['goal_scorer']
counts = assists_to_goals['count']

# Create a unique list of labels for assist makers and goal scorers
labels = list(set(assist_makers).union(set(goal_scorers)))
source_indices = [labels.index(assist_maker) for assist_maker in assist_makers]
target_indices = [labels.index(goal_scorer) for goal_scorer in goal_scorers]

#create Sankey graph
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=15,
        thickness=20,
        line=dict(color="black", width=0.5),
        label=labels,
        color="red"
    ),
    link=dict(
        source=source_indices,
        target=target_indices,
        value=counts
    ))])

fig.update_layout(title_text="Galatasaray 2023-2024 Season Assists Between Players", font_size=14)
fig.write_html("galatasaray_2023_2024_season_assists_to_goals.html")