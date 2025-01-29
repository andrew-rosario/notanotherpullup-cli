import requests,json
import sqlite3
import logging

def initialize_database():
    """
    Initializes the database with the schema.sql file
    :raises: Exception if the database already exists.
    """
    
    if os.path.exists("database.db"):
        raise Exception("Database already exists. Please delete the database.db file before running this function.")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    try:
        with open('../schema.sql','r') as file:
            schema = file.read()
            conn.executescript(schema)
    except FileNotFoundError:
        os.remove("database.db")
        raise Exception("schema.sql file not found.")
    except Exception as e:
        os.remove("database.db")
        raise e
    
    conn.commit()

def connect_database():
    """
    Connect to the database.
    :raises: Exception if the database does not exist.
    """
    
    if not os.path.exists("database.db"):
        raise Exception("Database does not exist. Please run the initialize_database function.")
    return sqlite3.connect("database.db")

    
def get_all_initial_workouts(api_key,api_endpoint="https://api.hevyapp.com/v1/"):
    """
    Compile all the Hevy workouts from the API into a Python list (of dictionaries).
    :return: A list of all the workouts.
    """
    
    current_page_number = 1
    page_count = -1
    final_list = []
    while current_page_number <= page_count or page_count == -1:
        # Use the api_endpoint, iterating through each page of the workouts with the maximum page size of 10.
        response = requests.get(api_endpoint + "workouts?page=" + str(current_page_number) + "&pageSize=10",headers={"api-key":api_key})
        current_page_dict = response.json()
        if page_count == -1:
            page_count = current_page_dict["page_count"]
  
        for workout in current_page_dict["workouts"]:
            final_list.append(workout)
        
        percent = round((current_page_number/page_count)*100, 2)
        print("Progress " + str(percent) + "%.")
        logging.debug("Finished compiling page " + str(current_page_number) + " of workouts.")
        current_page_number += 1

    print("Finished compiling all workouts.")
        
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
        conn.commit()
        
        for exercise in workout["exercises"]:
            exercise_index = exercise["index"]
            exercise_title = exercise["exercise_title"]
            exercise_notes = exercise["exercise_notes"]
            
            cursor.execute("INSERT INTO exercises "
                           "VALUES (?,?,?,?,?)",
                           (workout_id,exercise_id,exercise_index,exercise_title,exercise_notes))
            
            conn.commit()
            
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
                
                conn.commit()
                
                set_id += 1
                
            exercise_id += 1         
    
    cursor.close()
    conn.close()
def main_menu(api_key):
    """
    The main menu for the CLI.
    :param: api_key: The API key for the Hevy account.
    """
    
    print("Welcome to Not Another Pullup -- CLI.")
    print("Checking if the API can be reached...")
    
    response = requests.get("https://api.hevyapp.com/v1/workouts/count",headers={"api-key":api_key})
    if response.status_code != 200:
        print("The API could not be reached. Please check your API key, otherwise the API may be down.")
        sys.exit(0)
    
    if not os.path.exists("database.db"):
        print("I cannot find a database. Do you want to create a new one using the data currently on your account?")
        print("1. Yes")
        print("Anything else. (This will exit the application.)")
        response = input("Please select an option: ")
        if response == "1":
            initialize_database()
            populate_database(api_key)
        else:
            sys.exit(0)
            
    done = False
    while not done:
                
        menu_options = ["Update the database.",
                        "Rebuild database.",
                        "Search notes.",
                        "Search workouts.",
                        "Search exercise templates.",
                        "Quit."]
        menu_string = ""
        for i in range(len(menu_options)):
            menu_string += str(i+1) + ". " + menu_options[i] + "\n"
        menu_string = menu_string[:-2]
        print(menu_string)
        
        response = input("Please select an option: ")
        
        if response == "6":
            sys.exit(0)
    
    
def main():
    api_key = input("Please input the API key. (If you need help, please type 'help'): ")
    if api_key == "help":
        print("Please log on to the Hevy website on your browser (https://hevy.com), go to Settings, click on Developer, and generate an API key.\n"
              "This application only works for Hevy Pro users.")
    else:
        main_menu(api_key)
        
main()