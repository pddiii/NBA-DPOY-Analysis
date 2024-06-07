# %% [markdown]
# # Data
# 
# - In this chunk, I'm loading in the csv files I have collected for NBA data.
# - The `defense_dashboard`, `box_outs`, `defense_2pt`, `defense_3pt`, and `hustle_stats` objects were collected from NBA.com statistics using a Data Scraper.
#   - All from the 2023-2024 NBA Regular Season
# - The `dpoy_voting` data was collected from [Basketball-Reference ](https://www.basketball-reference.com/awards/awards_2024.html#all_dpoy)
#   - All NBA Regular Seasons from 2013-2014 through 2023-2024

# %%
import pandas as pd
import unidecode
import re

# create a function for standardizing the 'Player' column text across the dataframes
def clean_player_column(df):
    if 'Player' in df.columns:
        df['Player'] = df['Player'].apply(lambda x: unidecode.unidecode(x).lower()) # conver to lower case
        df['Player'] = df['Player'].apply(lambda x: re.sub(r'[^\w\s]', '', x))  # Remove punctuation
    return df

# load in the csv files containing the NBA.com data
defense_dashboard = clean_player_column(pd.read_csv('data/defense_dashboard.csv'))
box_outs = clean_player_column(pd.read_csv('data/box_outs.csv'))
defense_2pt = clean_player_column(pd.read_csv('data/defense_2pt.csv'))
defense_3pt = clean_player_column(pd.read_csv('data/defense_3pt.csv'))
hustle_stats = clean_player_column(pd.read_csv('data/hustle_stats.csv'))

# load voting information for defensive player of the year from Basketball-Reference
dpoy_voting = clean_player_column(pd.read_csv('data/dpoy_voting.csv'))

# load the teams data sourced from Stathead
teams_data = clean_player_column(pd.read_csv('data/stathead_team_stats.csv'))
teams_advanced = clean_player_column(pd.read_csv('data/stathead_team_advanced.csv'))

# load the player data sourced from Stathead
players_advanced = clean_player_column(pd.read_csv('data/stathead_player_advanced.csv'))
players = clean_player_column(pd.read_csv('data/stathead_player.csv'))

combine_metrics = pd.read_csv('data/nba_combine_data.csv').rename(columns={'PLAYER': 'Player'})
combine_metrics = clean_player_column(combine_metrics)

wingspans = clean_player_column(pd.read_csv('data/wingspans.csv'))
wingspans['Player'] = wingspans['Player'].str.split('\n').str[0]

# %% [markdown]
# Need to check the columns to see which ones we want, and if there are columns to be renamed.

# %%
# view the columns of the dataframes
dfs = [defense_dashboard, box_outs, defense_2pt, defense_3pt, hustle_stats, dpoy_voting]
for df in dfs:
    print(df.columns)

# %%
# Select only the specified columns for dpoy_voting
dpoy_voting = dpoy_voting[['Player', 'Age', 'Tm', 'Season', 'DPOY', 'First', 'Pts Won', 
                           'Pts Max', 'Share',  'G', 'MP', 'STL', 'BLK', 
                           'DWS', 'DBPM', 'DRtg']]


# Filter the 2023-24 DPOY Voting candidates
dpoy_24 = dpoy_voting[dpoy_voting['Season'] == '2023-24']

# change column names to be more specific
defense_2pt.rename(columns={'DFGM': 'DFGM_2pt', 'DFGA': 'DFA_2pt', 'DFG_PCT': 'DFG_pct_2pt'}, inplace=True)
defense_3pt.rename(columns={'DFGM': 'DFGM_3pt', 'DFGA': 'DFA_3pt', 'DFG_PCT': 'DFG_pct_3pt'}, inplace=True)

# %% [markdown]
# # Filter the 2024 DPOY Candidates

# %%
# Merge all other dataframes
data = pd.merge(defense_dashboard, box_outs, on=['Player', 'Season'], how='left')
data = pd.merge(data, defense_2pt.drop(columns=['Team', 'Age', 'Position', 'GP', 'FG_PCT']), 
                on=['Player', 'Season'], how='left')
data = pd.merge(data, defense_3pt.drop(columns=['Team', 'Age', 'Position', 'GP', 'FG_PCT']), 
                on=['Player', 'Season'], how='left')
data = pd.merge(data, hustle_stats.drop(columns=['Min']), on=['Player', 'Season'], how='left')

# Finally merge with dpoy_voting
data = pd.merge(data, dpoy_voting.drop(columns='Age'), on=['Player', 'Season'], how='left')

# Sort the data
data = data.sort_values(by=['Season', 'Pts Won'], ascending=[False, False])
data = data.sort_values(by='Season', ascending=False)

# Rename the columns to avoid confusion with total stats
data.rename(columns = {'BLK': 'BPG', 'STL': 'SPG'}, inplace=True)

# Create total stats columns
data['BLK'] = data['BPG'] * data['GP']
data['STL'] = data['SPG'] * data['GP']

# View the columns of data
print(data.columns)
# View the dimensions of the data
## 2462 rows, 41 columns
print(data.shape)

# %% [markdown]
# # Rank the Players
# - I decided to add variables ending in '_rank' in order to rank the players by their respective performance in each category
# - `higher_is_better` indicates the columns in which a higher value indicates a positive trend. 
#   - e.g. You draw more charges than another guy, that's a defensive benefit
# - `lower_is_better` indicates the columns in which a lower value indicates better performance
#   - e.g. Lower Defended Field Goal % often (but not always!) indicates better defense

# %%
higher_is_better = ['Deflections',  'charges', 'contested_shots', 'BLK', 'STL', 'DBPM']

lower_is_better = ['DFGM', 'DFG_PCT', 'DFG_pct_2pt', 'DFG_pct_3pt']

# create rankings for each of the columns
for col in higher_is_better:
    data[col + '_rank'] = data.groupby('Season')[col].rank(ascending=False)
# create rankings for each of the columns
for col in lower_is_better:
    data[col + '_rank'] = data.groupby('Season')[col].rank(ascending=True)
    
# filter the rankings columns for analysis
rankings = data.filter(regex='_rank$')

# %%
# calculate the avergage rank for each player
data['average_rank'] = rankings.mean(axis=1)
# sort the values by first by most recent season then by descending average rankings
data = data.sort_values(by=['Season', 'average_rank'], ascending=[False, True]).reset_index(drop=True)

# %% [markdown]
# # Cleaning the Team Data

# %%
# team opponent statistics need to rename columns to avoid confusion
rename_cols = teams_data.iloc[:, list(range(11, 23))].columns

# create a dictionary to rename the columns
rename_dict = dict(zip(rename_cols, ['opp_' + col for col in rename_cols]))

# rename the columns
teams_data = teams_data.rename(columns=rename_dict)

# create efficiency columns for the following opponent statistics
teams_data['opp_FG_pct'] = (teams_data['opp_FG'] / teams_data['opp_FGA']) * 100
teams_data['opp_2P_pct'] = (teams_data['opp_2P'] / teams_data['opp_2PA']) * 100
teams_data['opp_3P_pct'] = (teams_data['opp_3P'] / teams_data['opp_3PA']) * 100
teams_data['opp_FT_pct'] = (teams_data['opp_FT'] / teams_data['opp_FTA']) * 100

# drop the columns used to create the pct columns
teams_data.drop(columns=['G', 'STL', 'opp_FG', 'opp_FGA', 'opp_2P', 'opp_2PA', 'opp_3P', 'opp_3PA', 'opp_FT', 'opp_FTA'], 
                inplace=True)

# Rename the columns with the prefix 'tm_' to distinguish team variables in `data` object
rename_cols = list(teams_data.iloc[:, list(range(7, 17))].columns)
# create the dictionary for renaming the columns
rename_dict = dict(zip(rename_cols, ['tm_' + col for col in rename_cols]))
# rename the columns
teams_data = teams_data.rename(columns=rename_dict)
# sort the data with the oldest season first
teams_data.sort_values(by='Season', ascending=True, inplace=True)

# add 'opp_' prefix to advanced team statistics of the opponent
rename_cols = teams_advanced.iloc[:, list(range(13, 17))].columns
rename_dict = dict(zip(rename_cols, ['opp_' + col for col in rename_cols]))
teams_advanced = teams_advanced.rename(columns=rename_dict)

# convert the following columns to percentages
teams_advanced['opp_eFG%'] = teams_advanced['opp_eFG%'] * 100
teams_advanced['opp_TS%'] = teams_advanced['opp_TS%'] * 100

# repeat the process of prefixing 'tm_' to the columns in order to prevent confusion within data object.
rename_cols = list(teams_advanced.iloc[:, list(range(7, 18))].columns)
rename_dict = dict(zip(rename_cols, ['tm_' + col for col in rename_cols]))
teams_advanced = teams_advanced.rename(columns=rename_dict)

# Drop columns from the teams_advanced dataframe that are not needed
teams_advanced.drop(columns=['Rk', 'G', 'W', 'L', 'W/L%', 'G', 'tm_FTr'], inplace=True)
teams_advanced.sort_values(by='Season', ascending=True, inplace=True)

# %% [markdown]
# We now want to add the data from both `teams_advanced` and `teams_data` that we are interested in analyzing to the large dataframe `data`.

# %%
# add the teams_data variables to the data object
data = pd.merge(data, teams_data, on=['Team', 'Season'], how='left')
# add the teams_advanced variables to the data object
data = pd.merge(data, teams_advanced, on=['Team', 'Season'], how='left')
# drop the columns with the missing data
data.drop(columns=['STL', 'BLK', 'DWS', 'DBPM', 'DRtg', 'G', 'MP', 'Tm'], inplace=True)

# add the advanced player statistics to the data object for those players who were missing values
data = pd.merge(data, players_advanced[['Player', 'Season', 'STL', 'BLK', 'DWS', 'DBPM', 'DRtg']], 
                on=['Player', 'Season'], how='left')

# Distinguish the columns of the data with nan values
na_cols = ['DPOY', 'First', 'Pts Won', 'Pts Max', 'Share']
# fill the nan values with 0
data[na_cols] = data[na_cols].fillna(0)

# %%
# from nba_api.stats.static import teams
# from nba_api.stats.endpoints import commonteamroster
# from time import sleep
# from requests.exceptions import ReadTimeout

# nba_teams = teams.get_teams()
# nba_teams = pd.DataFrame(nba_teams)
# team_ids = nba_teams['id']

# rosters = []

# for id in team_ids:
#     for season in range(2013, 2024):
#         while True:
#             try:
#                 roster = commonteamroster.CommonTeamRoster(team_id=id, season=season).get_data_frames()[0]
#                 rosters.append(roster)
#                 break
#             except ReadTimeout:
#                 print("Timeout occurred for team_id: {}, season: {}. Retrying...".format(id, season))
#                 sleep(5)  # wait for 5 seconds before retrying


# rosters = pd.concat(rosters, ignore_index=True)

# rosters.to_csv('data/rosters.csv')
rosters = pd.read_csv('data/rosters.csv')

# Rename the columns
rosters.columns = rosters.columns.str.capitalize()

# fix the 'Player' column
rosters = clean_player_column(rosters)

# Modify the 'Season' column
rosters['Season'] = rosters['Season'].apply(lambda x: f"{x}-{str(int(x)+1)[-2:]}")

# function for converting the height to inches
def height_to_inches(height):
    feet, inches = height.split('-') # split them into separate variables
    return int(feet) * 12 + int(inches) # return the total inches

# fix the heights from the `rosters` dataframe
rosters['Height'] = rosters['Height'].apply(height_to_inches)

# add the Height and Weight variables to the data object
data = pd.merge(data, rosters[['Season', 'Player', 'Height', 'Weight']], on=['Player', 'Season'], how='inner')

# add the total defensive rebounds to the data object
data = pd.merge(data, players[['Player', 'Season', 'DRB', 'MP']], on=['Player', 'Season'], how='inner')

# Define a dictionary for the replacements
replacements = {'C-F': 'C', 'F-C': 'F', 'F-G': 'F', 'G-F': 'G'}

# Replace the values
data.replace(replacements, inplace=True)

# save the data to a csv file
# data.to_csv('data/clean.csv')

# %%
# from selenium import webdriver
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import pandas as pd

# # Function to generate season strings
# def generate_season_years(start_year, end_year):
#     season_years = []
#     for year in range(start_year, end_year + 1):
#         season_year = f"{year}-{str(year + 1)[-2:]}"
#         season_years.append(season_year)
#     return season_years

# # Generate list of season years from 2000-01 to 2024-25
# season_years = generate_season_years(2000, 2024)

# # Set up the WebDriver
# driver = webdriver.Chrome()

# all_data = []

# # Iterate through each season and scrape the data
# for season in season_years:
#     url = f"https://www.nba.com/stats/draft/combine-anthro?SeasonYear={season}"
#     driver.get(url)

#     try:
#         # Wait for the table to load
#         wait = WebDriverWait(driver, 10)
#         table = wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))

#         # Extract headers
#         headers = [header.text for header in table.find_elements(By.TAG_NAME, 'th')]

#         # Extract rows
#         rows = []
#         for row in table.find_elements(By.TAG_NAME, 'tr')[1:]:
#             cells = row.find_elements(By.TAG_NAME, 'td')
#             rows.append([cell.text.strip() for cell in cells])

#         # Create a DataFrame for the current season
#         df = pd.DataFrame(rows, columns=headers)
#         df['Season'] = season  # Add a season column
#         all_data.append(df)

#     except Exception as e:
#         print(f"Failed to retrieve data for season {season}: {e}")

# # Close the WebDriver
# driver.quit()

# # Concatenate all DataFrames
# combine_metrics = pd.concat(all_data, ignore_index=True)

# # Display the final DataFrame
# print(combine_metrics)

# Optionally, save to a CSV file
# combine_metrics.to_csv('nba_combine_data.csv', index=False)

# # Set up the WebDriver
# driver = webdriver.Chrome()

# # URL to scrape
# url = "https://craftednba.com/player-traits/length"

# # Open the webpage
# driver.get(url)

# # Wait for the table to load
# wait = WebDriverWait(driver, 20)
# table = wait.until(EC.presence_of_element_located((By.XPATH, '//table')))

# # Extract headers
# headers = [header.text for header in table.find_elements(By.XPATH, './/thead//th')]

# # Extract rows
# rows = []
# for row in table.find_elements(By.XPATH, './/tbody//tr'):
#     cells = row.find_elements(By.XPATH, './/td')
#     rows.append([cell.text.strip() for cell in cells])

# # Close the WebDriver
# driver.quit()

# # Create a DataFrame
# wingspans = pd.DataFrame(rows, columns=headers)

# # Display the DataFrame
# print(wingspans)

# # Optionally, save to a CSV file
# wingspans.to_csv('data/wingspans.csv', index=False)


# %%
print(wingspans['Player'])

# %%
import re
def convert_height_to_inches(height_str):
    try:
        # Use regular expressions to extract feet and inches
        match = re.match(r"(\d+)' ?(\d+\.?\d*)''", height_str)
        if match:
            feet = int(match.group(1))
            inches = float(match.group(2))
            # Convert to total inches
            total_inches = feet * 12 + inches
            return total_inches
        else:
            print(f"Failed to match: {height_str}")
            return None
    except Exception as e:
        print(f"Error processing {height_str}: {e}")
        return None
    
def wingspan_to_inches(wingspan_str):
    try:
        # Use regular expressions to extract feet and inches
        match = re.match(r"(\d+)' *(\d+\.?\d*)\"", wingspan_str)
        if match:
            feet = int(match.group(1))
            inches = float(match.group(2))
            # Convert to total inches
            total_inches = feet * 12 + inches
            return total_inches
        else:
            print(f"Failed to match: {wingspan_str}")
            return None
    except Exception as e:
        print(f"Error processing {wingspan_str}: {e}")
        return None

# Apply the conversion to the DataFrame columns
combine_metrics['HEIGHT W/O SHOES (in)'] = combine_metrics['HEIGHT W/O SHOES'].apply(convert_height_to_inches)
combine_metrics['HEIGHT W/ SHOES (in)'] = combine_metrics['HEIGHT W/ SHOES'].apply(convert_height_to_inches)
combine_metrics['STANDING REACH (in)'] = combine_metrics['STANDING REACH'].apply(convert_height_to_inches)
combine_metrics['WINGSPAN (in)'] = combine_metrics['WINGSPAN'].apply(convert_height_to_inches)

combine_metrics['BODY FAT %'] = combine_metrics['BODY FAT %'].astype('str').str.rstrip('%')

combine_metrics['BODY FAT %'] = pd.to_numeric(combine_metrics['BODY FAT %'], errors='coerce')

wingspans['Wingspan'] = wingspans['Wingspan'].apply(wingspan_to_inches)
wingspans.rename(columns={'Length': 'length_ratio'}, inplace=True)

data = pd.merge(data, combine_metrics.drop(columns='Season'), on='Player', how='left')
data = pd.merge(data, wingspans.drop(columns='Height'), on='Player', how='left')

# data.to_csv('data/clean.csv', index=False)


