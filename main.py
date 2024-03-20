import gspread
import statbotics
import json
import requests
import datetime


constants = open("./json-files/constants.json")
constant = json.load(constants)
constants.close()
team_number_column = constant["team_number_column"]
team_name_column = constant["team_name_column"]
team_state_column = constant["team_state_column"]
team_divison_column = constant["team_divison_column"]
team_epa_column = constant["team_epa_column"]
team_winrate_column = constant["team_winrate_column"]
spreadsheet_name = constant["spreadsheet_name"]
team_rookie_year_column = constant["team_rookie_year_column"]


auth_key = open("./json-files/X-TBA-Auth-Key.json")
key = json.load(auth_key)
auth_key.close()

stats = statbotics.Statbotics()
TBA_AUTH_KEY = key["key"]
TBA_BASE_ENDPOINT = "https://www.thebluealliance.com/api/v3"

gc = gspread.service_account(filename="json-files/credentials.json")

# Open a sheet from a spreadsheet in one go
sheet = gc.open(spreadsheet_name).sheet1
print(sheet.url)

event_keys = [
    "2024miwmi"
]


def call_tba_api(url):
    r = requests.get(f"{TBA_BASE_ENDPOINT}/{url}", headers={"X-TBA-Auth-Key": TBA_AUTH_KEY})

    return r.json()


def update_event_json():
    for event in event_keys:
        with open(f"./json-files/{event}.json", "w+") as jsonFile:
            data = call_tba_api(f"/event/{event}/teams")
            print(json.dumps(data))
            jsonFile.write(json.dumps(data))


def update_sheet():
    # update json files for entered event keys
    update_event_json()
    # create lists that will store gathered data so that we can push all the data in one go
    team_numbers = []
    team_names = []
    team_states = []
    team_epas = []
    team_winrates = []
    rookie_years = []
    rookies = []

    # store team numbers, names, and state/provinces
    for event in event_keys:
        with open(f"./json-files/{event}.json", "r") as data:
            data = json.load(data)
            for item in data:
                team_numbers.append([item["team_number"]])
                team_names.append([item["nickname"]])
                team_states.append([item["state_prov"]])

    # store team epas, winrates, and rookie years
    for team in team_numbers:
        team_epas.append([stats.get_team(team[0])["norm_epa"]])
        team_winrate = round(stats.get_team(team[0])["winrate"] * 100, 1)
        team_winrates.append([f"{team_winrate}%"])
        rookie_years.append([stats.get_team(team[0])["rookie_year"]])

    # use batch update to avoid google requests rate limit
    sheet.batch_update([{
        "range": f"{team_number_column}2:{team_number_column}{len(team_numbers) + 1}",
        "values": team_numbers
    }])

    sheet.batch_update([{
        "range": f"{team_name_column}2:{team_name_column}{len(team_names) + 1}",
        "values": team_names
    }])

    sheet.batch_update([{
        "range": f"{team_state_column}2:{team_state_column}{len(team_states) + 1}",
        "values": team_states
    }])

    sheet.batch_update([{
        "range": f"{team_epa_column}2:{team_epa_column}{len(team_epas) + 1}",
        "values": team_epas
    }])

    sheet.batch_update([{
      "range": f"{team_winrate_column}2:{team_winrate_column}{len(team_winrates) + 1}",
      "values": team_winrates
    }])

    sheet.batch_update([{
        "range": f"{team_rookie_year_column}2:{team_rookie_year_column}{len(rookie_years) + 1}",
        "values": rookie_years
    }])


update_sheet()
