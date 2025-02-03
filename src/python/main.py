import requests,json
import sqlite3
import os, sys
import logging

class NotAnotherPullupMain:
    
    def __init__(self, api_key) -> None:
        try:
            assert len(api_key) > 0
        except AssertionError:
            raise Exception("API key is empty. This class cannot function without an API key.")
        self.api_key = api_key
    def initialize_database(self) -> None:
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

    def connect_database(self) -> sqlite3.Connection:
        """
        Connect to the database.
        :raises: Exception if the database does not exist.
        """
        
        if not os.path.exists("database.db"):
            raise Exception("Database does not exist. Please run the initialize_database function.")
        return sqlite3.connect("database.db")

    def get_all_initial_workouts(self,api_endpoint="https://api.hevyapp.com/v1/") -> list:
        """
        Compile all the Hevy workouts from the API into a Python list (of dictionaries).
        :return: A list of all the workouts.
        """
        
        # TODO: Save the data as a JSON, so I don't have to keep calling the API.
        
        current_page_number = 1
        page_count = -1
        final_list = []
        while current_page_number <= page_count or page_count == -1:
            # Use the api_endpoint, iterating through each page of the workouts with the maximum page size of 10.
            response = requests.get(api_endpoint + "workouts?page=" + str(current_page_number) + "&pageSize=10",headers={"api-key":self.api_key})
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

    def populate_database(self,start_clean=True) -> None:
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
            self.initialize_database()
        
        conn = self.connect_database()
        
        workouts = self.get_all_initial_workouts()
        
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
                exercise_title = exercise["title"]
                exercise_notes = exercise["notes"]
                
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
            
    def get_iso8601_date_from_string(self,date_string) -> str:
        """
        Convert a date string to an ISO8601 (ie. 1970-01-01T00:00:00Z) formatted date string with no offset.
        It accepts dates formatted only in MM/DD/YYYY. (Sorry, everywhere except Canada and United States.)
        :param date_string: The date string to convert.
        :return: The ISO8601 formatted date string.
        """
        
        components = date_string.split("/")
        string = components[2]
        string += "-"
        
        string += components[0]
        string += "-"
        
        string += components[1]
        string += "T00:00:00Z"
        
        return string

    def get_recent_workout_changes(self,date_since, api_endpoint="https://api.hevyapp.com/v1/") -> list:
        """
        Use the Hevy API events endpoint to get a list of workout updates since a specific date.
        This includes new, modified, and deleted workouts.
        
        Please see the README for how the API delivers the JSON response.
        
        :param date: The date to get the updates since, in ISO8601 format. (Example: "2021-01-01T00:00:00Z") (Note that hours and seconds matters; for the entire day, specify midnight. Offsets are not supported.)
        """
        updates = None
        current_page = 1
        page_count = None
        
        # Replace the colons in the date string with %3A to make it URL-safe.
        new_str = []
        for c in date_since:
            if c == ":":
                new_str += "%3A"
            else:
                new_str += c
        
        date_since = "".join(new_str)
            
        while current_page <= page_count or page_count is None:
            response = requests.get(api_endpoint + "/workouts/events?page" + str(current_page) + "&pageSize=10&since=" + date_since,headers={"api-key":self.api_key})
            current_page = response.json()
            if page_count is None:
                page_count = current_page["page_count"]
            
            if updates is None:
                updates = current_page["events"]
            else:
                for event in current_page["events"]:
                    updates += event
            current_page += 1
        return updates
    def update_workout_locally(self,workout_id, data):
        """
        Update the workout (if it exists) with the given data.
        :param: workout_id, the workout ID to update.
        :param: data, the data to update the workout with.
        """
        
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,))
        result = cursor.fetchall()
        
        if result is None:
            raise Exception("Workout not found.")
        elif len(result) > 1:
            raise Exception("More than one workout is found with this ID, somehow.")
        else:
            title = data["title"]
            description = data["description"]
            start_time = data["start_time"]
            end_time = data["end_time"]
            updated_at = data["updated_at"]
            created_at = data["created_at"]
            
            cursor.execute("UPDATE workouts SET "
                        "title=?,description=?,start_time=?,end_time=?,update_time=?,creation_time=? "
                        "WHERE id =?",(title,description,start_time,end_time,updated_at,created_at,workout_id))
            conn.commit()
        
        cursor.close()
        conn.close()
            
    def add_workout_locally(self,workout):
        """
        Add a workout to the database with the given data.
        :param: workout, a dictionary with the workout data.
        """
        
        id_to_search = workout["id"]
        
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workouts WHERE id = ?",(id_to_search,))
        result = cursor.fetchall()
        if len(result) is not None:
            raise Exception("There already exists a workout with this ID.")
        else:
            workout_id = workout["id"]
            title = workout["title"]
            description = workout["description"]
            start_time = workout["start_time"]
            end_time = workout["end_time"]
            updated_at = workout["updated_at"]
            created_at = workout["created_at"]
            
            cursor.execute("INSERT INTO workouts "
                        "VALUES (?,?,?,?,?,?,?)", (workout_id,title,description,start_time,end_time,updated_at,created_at))
            
            conn.commit()
        
        cursor.close()
        conn.close()
        
    def delete_workout_locally(self,workout_id):
        """
        Delete a workout in the database.
        :param: workout_id, in UUID format.
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM workouts WHERE id = ?",(workout_id,))
        conn.commit()
        cursor.close()
        conn.close()
def main():
    api_key = input("Please input the API key. (If you need help, please type 'help'): ")
    if api_key == "help":
        print("Please log on to the Hevy website on your browser (https://hevy.com), go to Settings, click on Developer, and generate an API key.\n"
              "This application only works for Hevy Pro users.")
    else:
        main_menu(api_key)
        
main()