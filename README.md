## Not Another Pullup CLI
This is the testing portion of the Not Another Pullup application, using this project as a way to dissect the Hevy API and to determine how to store workout data for the main application.

## Hevy Workout JSON Format

- Workout ID
- Title of Workout
- Description
- Start time
- End time
- Latest update time
- Creation time
- Exercises
  - Particular exercise
    - Exercise list index
    - Exercise title
    - Exercise notes
    - Exercise template ID
    - Superset ID
    - Sets
      - A particular set
        - Set list index
        - Set type (**normal, warmup, failure, dropset, etc.**)
        - Weight (in kilograms)
        - Reps count
        - Distance (in meters)
        - Duration (in seconds)
        - Rate of perceived exertion
      - ....
      - ...
  - ...
  - ...
-
