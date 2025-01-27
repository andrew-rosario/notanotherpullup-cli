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

def connect_database():
    
    return sqlite3.connect("database.db")

    
def get_all_initial_workouts(api_key,api_endpoint="https://api.hevyapp.com/v1/"):
    """
    Compile all the Hevy workouts from the API into a Python list (of dictionaries).
    :return: A list of all the workouts.
    """
    current_page = 1
    page_count = None
    final_list = None
    while current_page < page_count:
        # Use the api_endpoint, iterating through each page of the workouts with the maximum page size of 10.
        response = requests.get(api_endpoint + "workouts?page" + str(i) + "&pageSize=10",headers={"api-key":api_key})
        current_page = response.json()
        if page_count is None:
            page_count = current_page["page_count"]
        
        if final_list is None:
            final_list = current_page["workouts"]
        else: 
            for workout in current_page["workouts"]:
                final_list.append(workout)
            
        
        current_page += 1
        
    return final_list

def main():
    return None