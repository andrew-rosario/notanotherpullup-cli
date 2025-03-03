import requests,json
import sqlite3
import os, sys
from shutil import copy
from datetime import datetime, timezone
import logging

class NotAnotherPullupMain:
    
    def __init__(self, api_key) -> None:
        try:
            assert len(api_key) > 0
        except AssertionError:
            raise Exception("API key is empty. This class cannot function without an API key.")
        self.api_key = api_key
    
    def initiate_rebuild(self) -> None:
        """
        Rebuild the database.
        """
        os.remove("database.db")
        self.initialize_database()
        self.populate_database()

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

    def backup_database(self) -> None:
        """
        Backup the database.
        """
        current_date = datetime.now().strftime("%m-%d-%Y %H:%M:%S")
        copy("database.db","database_backups/"+current_date +"_database.db")
        
        try: 
            assert os.path.exists("database_backups/"+current_date +"_database.db")
        except AssertionError:
            raise Exception("Backup failed.")
        print("Backup successful.")

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

    def get_exercise_templates(self,api_endpoint="https://api.hevyapp.com/v1/") -> list:
        """
        Get all the exercise templates from the Hevy API.
        """
        
        # TODO: Make function that reuses the process of getting all JSON data from the API, then replace all instances of this process with the new function.
        
        # TODO: Add exercise_templates table to the database schema.
        
        # -------------------
        # Discussion:
        #  Hevy API does not have an API call for exercise template updates.
        #
        #  I have two options:
        # 1. Replace the table every time with the new data (which I have to do if I update the exercise table since a user might have done a workout with a new exercise template).
        # 2. Find a way to get the new exercise templates and add them to the table. (This is more efficient but the data lacks ANY timestamps.)
        # 
        # 3. I should crossreference all exercises in the workouts and see if any of them are not in the exercise_templates table. If they are not, that means there are new exercise templates. The API does provide a way to get a exercise template by ID, so this could work.
        
        # Honestly, option 1 is just easier for now. But option 3 is definitely the long-term solution.
        
        #-------------------
        
        current_page_number = 1
        page_count = -1
        final_list = []
        while current_page_number <= page_count or page_count == -1:
            # Okay, the base Hevy set of exercise templates is over 500. This page size now makes sense.
            response = requests.get(api_endpoint + "exercise_templates?page=" + str(current_page_number) + "&pageSize=100",headers={"api-key":self.api_key})
            current_page_dict = response.json()
            if page_count == -1:
                page_count = current_page_dict["page_count"]
                
            for exercise_template in current_page_dict["exercise_templates"]:
                final_list.append(exercise_template)

            percent = round((current_page_number/page_count)*100, 2)
            print("Progress " + str(percent) + "%.")
            logging.debug("Finished compiling page " + str(current_page_number) + " of exercise templates.")
            current_page_number += 1
        print("Finished compiling all exercise templates.")
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
        
        print("Populating database with workouts...")
        added_on = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        
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
                        "VALUES (?,?,?,?,?,?,?,?)",
                        (workout_id,title,description,start_time,end_time,updated_at,created_at,added_on))
            conn.commit()
            
            for exercise in workout["exercises"]:
                exercise_index = exercise["index"]
                exercise_title = exercise["title"]
                exercise_notes = exercise["notes"]
                exercise_template_id = exercise["exercise_template_id"]
                cursor.execute("INSERT INTO exercises "
                            "VALUES (?,?,?,?,?,?)",
                            (workout_id,exercise_id,exercise_index,exercise_title,exercise_notes,exercise_template_id))
                
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
                    
                if exercise_id % 20:
                    print("Finished adding workout " + workout_id + " to the database.")
                exercise_id += 1
            if exercise_id % 20:
                print("Finished adding workout " + workout_id + " to the database.")
                
 
        print("Finished adding all workouts to the database.")
        print("Adding exercise templates to the database...")
        exercise_templates = self.get_exercise_templates()
        
        # TODO: Make separate function for putting exercise templates into the table. Then replace this code with the function.
        
        muscle_group_ids = {}
        muscle_group_index = 1
        
        for exercise_template in exercise_templates:
            template_id = exercise_template["id"]
            title = exercise_template["title"]
            # Exercise type could be "weight_reps", "reps_only", "duration", "bodyweight_weighted", or "bodyweight_assisted".
            # I should go into the Hevy app and make one of each type to see what the API returns.
            exercise_type = exercise_template["type"]
            primary_muscle = exercise_template["primary_muscle_group"]
            
            if primary_muscle not in muscle_group_ids.keys():
                print("Muscle group " + primary_muscle + " not found in muscle_group. Adding to muscle_groups table.")
                muscle_group_ids[primary_muscle] = muscle_group_index
                cursor.execute("INSERT INTO muscle_groups "
                               "VALUES (?,?)",(muscle_group_index, primary_muscle))
                conn.commit()
                muscle_group_index += 1
                
            is_custom = exercise_template["is_custom"]
            
            cursor.execute("INSERT INTO exercise_templates "
                           "VALUES (?,?,?,?,?)",
                           (template_id,title,exercise_type,muscle_group_ids[primary_muscle],is_custom))
            
            conn.commit()
            # Do the same existence check for secondary muscle groups.
            template_index = 1
            secondary_muscle_group = exercise_template["secondary_muscle_groups"]
            for secondary_muscle in secondary_muscle_group:
                if secondary_muscle not in muscle_group_ids.keys():
                    muscle_group_ids[secondary_muscle] = muscle_group_index
                    
                    print("Muscle group " + secondary_muscle + " not found in muscle_group. Adding to muscle_groups table.")

                    cursor.execute("INSERT INTO muscle_groups "
                                   "VALUES (?,?)",(muscle_group_index, secondary_muscle))
                    conn.commit()
                    muscle_group_index += 1
                
                cursor.execute("INSERT INTO secondary_muscle_groups "
                               "VALUES (?,?)",
                               (template_id,muscle_group_ids[secondary_muscle]))
            conn.commit()
            
            if template_index % 20:
                print("Finished adding exercise template " + template_id + " to the database.")
            template_index += 1

        print("Finished adding all exercise templates to the database.")
                
            
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

    def get_latest_added_workout_date(self,api_endpoint="https://api.hevyapp.com/v1/") -> str:
        """
        Get the most recent workout date on the database.
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT MAX(added_on) FROM workouts")
        
        return cursor.fetchone()[0]

    def get_recent_workout_changes(self, api_endpoint="https://api.hevyapp.com/v1/") -> list:
        """
        Use the Hevy API events endpoint to get a list of workout updates since the last update.
        """
        
        updates = {"added":[],"updated":[],"deleted":[]}
        current_page = 1
        page_count = -1
        
        date_since = self.get_latest_added_workout_date()
        # Make it URL-safe.
        date_since = date_since.replace(":","%3A") 
                
                    
        while current_page <= page_count or page_count == -1:
            response = requests.get(api_endpoint + "workouts/events?page" + str(current_page) + "&pageSize=10&since=" + date_since,headers={"api-key":self.api_key})
            current_page_dict = response.json()
            if page_count == -1:
                page_count = current_page_dict["page_count"]
                
            if "events" not in current_page_dict.keys():
                break
           
            for event in current_page_dict["events"]:
                if event["type"] == "updated":
                    updates["updated"].append(event)
                elif event["type"] == "deleted":
                    updates["deleted"].append(event)
            
            current_page += 1
        return updates
    
    def update_database(self) -> None:
        updates = self.get_recent_workout_changes()
        
        if len(updates["updated"]) + len(updates["deleted"]) == 0:
            print("No updates found.")
        else:
            for event in updates["updated"]:
                conn = self.connect_database()
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM workouts WHERE id = ?",(event["workout"]["id"],))
                exists = cursor.fetchall()
                cursor.close()
                conn.close()
                if exists == []:
                    self.add_workout_locally(event["workout"])
                else:
                    self.update_workout_locally(event["workout"]["id"],event["workout"])
                
            for event in updates["deleted"]:
                self.delete_workout_locally(event["id"])
            print("Finished updating the database.")
            
    
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
        

        try:
            if result is None:
                print("Workout not found. There was nothing to update.")
            else:
                title = data["title"]
                print("Updating workout " + title + ".")

                description = data["description"]
                start_time = data["start_time"]
                end_time = data["end_time"]
                updated_at = data["updated_at"]
                created_at = data["created_at"]
                added_on = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                cursor.execute("UPDATE workouts SET "
                            "title=?,description=?,start_time=?,end_time=?,update_time=?,creation_time=?,added_on=? "
                            "WHERE id =?",(title,description,start_time,end_time,updated_at,created_at,added_on,workout_id))
                conn.commit()
        except KeyError:
            print("Data is missing. Workout was not updated.")
        
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
        if result != []:
            print("There already exists a workout with this ID. It was not added.")
        else:
            print("Adding workout.")
            workout_id = workout["id"]
            title = workout["title"]
            description = workout["description"]
            start_time = workout["start_time"]
            end_time = workout["end_time"]
            updated_at = workout["updated_at"]
            created_at = workout["created_at"]
            added_on = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            
            cursor.execute("INSERT INTO workouts "
                        "VALUES (?,?,?,?,?,?,?,?)", (workout_id,title,description,start_time,end_time,updated_at,created_at,added_on))
            
            conn.commit()
            print("Workout added.")
        
        cursor.close()
        conn.close()
        
    def delete_workout_locally(self,workout_id):
        """
        Delete a workout in the database.
        :param: workout_id, in UUID format.
        """
        conn = self.connect_database()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM workouts WHERE id = ?",(workout_id,))
        results = cursor.fetchall()
        if results is None:
            print("Workout not found. Nothing was deleted.")
        else:
            print("Deleting workout.")
            cursor.execute("DELETE FROM workouts WHERE id = ?",(workout_id,))
            conn.commit()
            print("Workout deleted.")
        cursor.close()
        conn.close()
        
class DatabaseUtilities:
    def __init__(self, database_path=""):
        self.database_path = database_path
        try:
            if not os.path.isfile(database_path):
                raise Exception("Database does not exist.")
            self.conn = sqlite3.connect(database_path)
            self.cursor = self.conn.cursor()
        except Exception as e:
            raise e
        
    def get_all_exercise_notes(self,descending=True):
        try:
            assert self.conn is not None
            assert self.cursor is not None
        except AssertionError:
            raise Exception("Database connection not established.")
        
        
        query = "SELECT workouts.creation_time, exercises.exercise_title, exercises.exercise_notes FROM workouts INNER JOIN exercises ON workouts.id = exercises.workout_id WHERE exercises.exercise_notes != '' ORDER BY workouts.creation_time"
        
        query += " DESC" if descending else " ASC"
        
        results = self.cursor.execute(query)
        return results.fetchall()

    def get_notes_by_keyword(self,keyword, descending=True):
        try:
            assert self.conn is not None
            assert self.cursor is not None
        except AssertionError:
            raise Exception("Database connection not established.")
        
        query = "SELECT workouts.creation_time, exercises.exercise_title, exercises.exercise_notes FROM workouts INNER JOIN exercises ON workouts.id = exercises.workout_id WHERE exercises.exercise_notes LIKE ?"
        
        query += " DESC" if descending else " ASC"

        
        results = self.cursor.execute(query,("%" + keyword + "%",))
        return results.fetchall()
    def get_notes_by_exercise_name(self,exercise_name, descending=True):
        query = "SELECT exercises.notes, workout.creation_date FROM exercises INNER JOIN workouts ON exercises.workout_id = workouts.id WHERE exercises.exercise_title = ? ORDER BY workouts.creation_date"

        query += " DESC" if descending else " ASC"
        self.cursor.execute(query, (exercise_name,))

    def get_exercise_name_by_template_id(self,template_id):
        query = "SELECT exercise_title FROM exercise_templates WHERE id = ?"
        
        results = self.cursor.execute(query,(template_id,))
        return results.fetchone()
    
    def get_template_id_by_exercise_name(self,exercise_name):
        query = "SELECT id FROM exercise_templates WHERE exercise_title = ?"
        
        results = self.cursor.execute(query,(exercise_name,))
        return results.fetchone()
    
    def get_all_workouts(self, descending=True):
        query = "SELECT title,creation_time,id FROM workouts" +" ORDER BY creation_time"
        query += " DESC" if descending else " ASC"
        
        results = self.cursor.execute(query)
        return results.fetchall()
    def convert_kg_to_lbs(self,kg,truncate=False):
        # Most gyms only do .5 increments for pounds, so I should truncate the result if the user wants.
        if truncate:
            return round(kg * 2.20462,1)
        else:
            return kg * 2.20462
class CLInterface:
    def __init__(self, api_key):
        self.api_key = api_key
        self.client = None
        self.database_util = None
        
    def menu_printer(self,menu_options):
        menu_string = ""
        for i in range(len(menu_options)):
            menu_string += str(i+1) + ". " + str(menu_options[i]) + "\n"
        menu_string = menu_string[:-1]
        print(menu_string)

    def main_menu(self):
        """
        The main menu for the CLI.
        :param: api_key: The API key for the Hevy account.
        """
        
        print("Welcome to Not Another Pullup -- CLI.")
        print("Checking if the API can be reached...")
        
        response = requests.get("https://api.hevyapp.com/v1/workouts/count",headers={"api-key":self.api_key})
        if response.status_code != 200:
            print("The API could not be reached. Please check your API key, otherwise the API may be down.")
            sys.exit(0)
        else:
            print("Wow, you've done " + str(response.json()["workout_count"]) + " workouts. That's impressive.") if response.json()["workout_count"] != 0 else print("You haven't done any workouts yet... Girl, you better get to work.")
        
        self.client = NotAnotherPullupMain(self.api_key)
        
        if not os.path.exists("database.db"):
            print("I cannot find a local database. Do you want to create a new one using the data currently on your account?")
            print("1. Yes")
            print("Anything else. (This will exit the application.)")
            response = input("Please select an option: ")
            if response == "1":
                self.client.initialize_database()
                self.client.populate_database(self.api_key)
            else:
                sys.exit(0)
                
        done = False
        
        self.database_util = DatabaseUtilities("database.db")
        while not done:
            print("--- Main Menu ---")
            menu_options = ["Database operations.",
                            "Get data.",
                            "Search data.",
                            "Calculate insights.",
                            "Quit."]
            self.menu_printer(menu_options)
            
            response = input("Please select an option: ")
            actual_response = menu_options[int(response)-1]
            
            # This is to accommodate adding more options later.
            if actual_response == "Quit.":
                sys.exit(0)
            elif actual_response == "Database operations.":
                self.database_operations()
            elif actual_response == "Get data.":
                self.data_gathering()
            else:
                print("I didn't code that yet.")
    
    def database_operations(self):
        """
        The database operations menu.
        """
        done = False
        while not done:
            menu_options = ["Update database.",
                            "Rebuild database.",
                            "Backup database.",
                            "Go back to main menu."]
            
            self.menu_printer(menu_options)
            
            response = input("Please select an option: ")
            actual_response = menu_options[int(response)-1]
            
            if actual_response == "Go back to main menu.":
                done = True
            elif actual_response == "Update database.":
                print("Updating database...")
                self.client.update_database()
            elif actual_response == "Rebuild database.":
                print("This process will remove the current database and rebuild it. Are you sure you want to continue?")
                self.menu_printer(["Yes.","No."])
                try:
                    response = input("Please select an option: ")
                    actual_response = ["Yes.","No."][int(response)-1]
                except IndexError:
                    actual_response = "No."
    
                if actual_response == "Yes.":
                    self.client.initiate_rebuild()
                elif actual_response == "No.":
                    pass
            elif actual_response == "Backup database.":
                #TODO: Instantiate the menu options in a separate variable later.
                print("This will create a backup of the database. It will be saved as 'thecurrent dateandtime_backup.db.'")
                print("Are you sure you want to continue?")
                self.menu_printer(["Yes.","No."])
                try:
                    response = input("Please select an option: ")
                    actual_response = ["Yes.","No."][int(response)-1]
                except IndexError:
                    actual_response = "No."
    
                if actual_response == "Yes.":
                    self.client.backup_database()
                elif actual_response == "No.":
                    pass
    def data_gathering(self):
        done = False
        while not done:
            menu_options = ["Get all workouts.",
                            "Get all workout notes.",
                            "Get all exercises.",
                            "Get all exercise notes.",
                            "Get all exercise templates.",
                            "Get all muscle groups.",
                            "Go back to main menu."]
            self.menu_printer(menu_options)
            response = input("Please select an option: ")
            actual_response = menu_options[int(response)-1]
            
            if actual_response == "Go back to main menu.":
                done = True
            elif actual_response == "Get all workouts.":
                workouts = self.database_util.get_all_workouts()
                
                total_pages = len(workouts) // 10
                last_page_length = len(workouts) % 10
                
                if last_page_length: 
                    total_pages += 1
                
                perusing = True
                current_page = 1
                while perusing:
                    # Python slicing is inclusive for the start and exclusive for the end.

                    start_range = 10 * (current_page -1)
                    end_range = 10 * (current_page) if last_page_length != 0 else 10 * (current_page - 1) + last_page_length
                    
                    print("Page " + str(current_page) + "/" + str(total_pages))
                    page = workouts[start_range:end_range]
                    
                    self.menu_printer(page)
                    menu_options = ["Open workout.",
                                    "Next page.",
                                    "Previous page.",
                                    "Go to page number #.",
                                    "Go back to main menu."]
                    self.menu_printer(menu_options)
                    
                    response = input("Please select an option: ")
                    try:
                        response = int(response)
                        assert response > 0
                    except ValueError:
                        print("This is not a valid number.")
                    except AssertionError:
                        print("This is not a valid number.")
                        
                    
                    else:
                        actual_response = menu_options[response-1]
                        if actual_response == "Go back to main menu.":
                            perusing = False
                        elif actual_response == "Next page.":
                            if current_page == total_pages:
                                print("You are already on the last page.")
                            elif current_page < total_pages:
                                current_page += 1
                        elif actual_response == "Previous page.":
                            if current_page == 1:
                                print("You are already on the first page.")
                            elif current_page > 1:
                                current_page -= 1
                        elif actual_response == "Go to page number #.":
                            response = input("Please input the page number: ")
                            try:
                                current_page = int(response)
                                if current_page < 1 or current_page > total_pages:
                                    print("Invalid page number.")
                            except ValueError:
                                print("Invalid page number.")
                        elif actual_response == "Open workout.":
                            response = input("Select a workout number to open: ")
                            try:
                                workout = page[int(response)-1]
                            except IndexError:
                                print("Invalid workout number.")
                            except ValueError:
                                print("Not a valid number.")
                            else:
                                self.database_options.get_more_details_on_workout(workout[0])
            elif actual_response == "Get all workout notes.":
                perusing = True
                while perusing:
                    menu_options = ["Get all notes",
                                    "Get by exercise name.",
                                    "Get by date range.",
                                    "Go up one level."]
                    self.menu_printer(menu_options)
                    response = input("Please select an option: ")
                    actual_response = menu_options[int(response)-1]
                    
                    if actual_response == "Get all notes.":
                        # TODO: Find a way to put this code in a separate function because it is just too much, man. 
                        notes = self.database_util.get_all_exercise_notes()
                    elif actual_response == "Get by exercise name.":
                        exercise_name = input("Please input the exercise name: ")
                        notes = self.database_util.get_notes_by_exercise_name(exercise_name)
                    elif actual_response == "Get by date range.":
                        print("I haven't coded this yet.")
                    elif actual_response == "Go up one level.":
                        perusing = False
                    total_pages = len(notes) // 10
                    last_page_length = len(notes) % 10
                    
                    if last_page_length:
                        total_pages += 1
                        
                    current_page = 1
                    while perusing:
                        start_range = 10 * (current_page -1)
                        end_range = 10 * (current_page) if last_page_length != 0 else 10 * (current_page - 1) + last_page_length
                        
                        print("Page " + str(current_page) + "/" + str(total_pages))
                        page = notes[start_range:end_range]
                        
                        self.menu_printer(page)
                        menu_options = ["Next page.",
                                        "Previous page.",
                                        "Go to page number #.",
                                        "Go back to main menu."]
                        self.menu_printer(menu_options)
                        
                        response = input("Please select an option: ")
                        try:
                            response = int(response)
                            assert response > 0
                        except ValueError:
                            print("This is not a valid number.")
                        except AssertionError:
                            print("This is not a valid number.")
                        else:
                            actual_response = menu_options[response-1]
                            if actual_response == "Go back to main menu.":
                                perusing = False
                            elif actual_response == "Next page.":
                                if current_page == total_pages:
                                    print("You are already on the last page.")
                                elif current_page < total_pages:
                                    current_page += 1
                            elif actual_response == "Previous page.":
                                if current_page == 1:
                                    print("You are already on the first page.")
                                elif current_page > 1:
                                    current_page -= 1
                            elif actual_response == "Go to page number #.":
                                response = input("Please input the page number: ")
                                try:
                                    current_page = int(response)
                                    if current_page < 1 or current_page > total_pages:
                                        print("Invalid page number.")
                                except ValueError:
                                    print("Invalid page number.")
                
                    
              
def main():
    api_key = input("Please input the API key. (If you need help, please type 'help'): ")
    if api_key == "help":
        print("Please log on to the Hevy website on your browser (https://hevy.com), go to Settings, click on Developer, and generate an API key.\n"
              "This application only works for Hevy Pro users.")
    else:
        interface = CLInterface(api_key)
        interface.main_menu()
        
if __name__ == "__main__":
    main()