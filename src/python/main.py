import requests,json
import sqlite3
api_key = "1015d522-e3c1-49f7-9223-d275e947142a"

api_endpoint = "https://api.hevyapp.com/v1/"


def initialize_database():
    """
    Initializes the database with the schema.sql file
    """
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    with open('./schema.sql','r') as file:
        schema = file.read()
    
    cursor.executescript(schema)
    
    conn.commit()
    
    
def get_all_initial_workouts():
    i = 1
    done = False
    while not done:
        # Use the api_endpoint, iterating through each page of the workouts with the maximum page size of 10.
        response = requests.get(api_endpoint + "workouts?page" + str(i) + "&pageSize=10",headers={"api-key":api_key})
        data = response.json()

def main():
    return None