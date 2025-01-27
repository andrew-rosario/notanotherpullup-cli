import requests,json
import sqlite3
import os
api_key = "1015d522-e3c1-49f7-9223-d275e947142a"

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
    while current_page < page_count or page_count is None:
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
def populate_database(start_clean=True):
    """
    Populate the database with the initial workouts.
    (There may be unexpected behaviour if ran from any other instances.
    If you need to update the database, please run the update_database function instead.)
    :param start_clean: Whether to start with a clean database, default is True.
    """
    if start_clean:
        try:
            os.remove("database.db")
        except OSError:
            pass
        initialize_database()
    
    conn = connect_database()
     
    workouts = get_all_initial_workouts(api_key)
    
    exercise_id = 1
    set_id = 1
    
    for workout in workouts:
        cursor = conn.cursor()
        
        workout_id = workout["id"]
        title = workout["title"]
        description = workout["description"]
        start_time = workout["start_time"]
        end_time = workout["end_time"]
        updated_at = workout["updated_at"]
        created_at = workout["created_at"]
        
        cursor.execute("INSERT INTO workouts "
                       "VALUES (?,?,?,?,?,?,?)",
                       (workout_id,title,description,start_time,end_time,updated_at,created_at))
        cursor.commit()
        
        for exercise in workout["exercises"]:
            exercise_index = exercise["index"]
            exercise_title = exercise["exercise_title"]
            exercise_notes = exercise["exercise_notes"]
            
            cursor.execute("INSERT INTO exercises "
                           "VALUES (?,?,?,?,?)",
                           (workout_id,exercise_id,exercise_index,exercise_title,exercise_notes))
            
            cursor.commit()
            
            for set in exercise["sets"]:
                set_index = set["index"]
                set_type = set["type"]
                weight = set["weight_kg"]
                reps = set["reps"]
                distance = set["distance_meters"]
                duration = set["duration_seconds"]
                rpe = set["rpe"]
                
                cursor.execute("INSERT INTO sets "
                               "VALUES (?,?,?,?,?,?,?,?,?)",
                               (exercise_id,set_id,set_index,set_type,weight,reps,distance,duration,rpe))
                
                cursor.commit()
                
                set_id += 1
                
            exercise_id += 1         
    
    cursor.close()
    conn.close()
        
    
def main():
    return None