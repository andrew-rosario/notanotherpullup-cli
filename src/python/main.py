import requests,json
import sqlite3
api_key = "1015d522-e3c1-49f7-9223-d275e947142a"

api_endpoint = "https://api.hevyapp.com/v1/"


def initialize_database():
    conn = sqlite3.connect("database.sqlite3")

def get_all_initial_workouts():
    i = 1
    done = False
    while not done:
        response = requests.get(api_endpoint + "workouts?page" + str(i) + "&pageSize=10",headers={"api-key":api_key})
        data = response.json()



def main():
    return None