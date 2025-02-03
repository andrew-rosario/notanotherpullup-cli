# Not Another Pullup CLI

This is the testing portion of the Not Another Pullup application, using this project as a way to dissect the Hevy API and to determine how to store workout data for the main application.

Besides from helping me figure out the backend of this application, it also has some useful utility functions for Hevy Pro users.


### Planned Features

- Get the information you can already get in the app (PRs, most done exercises, all exercise templates, etc.)
- **Get all your notes** and **search** for them by keyword, date, workout, etc.
  - Inspiration: I was doing a workout and I wanted to look up where the safety bars were on a specific workout.
- **Filter for a particular workout** by keyword and time range, or even workout ID (if you know that).
  - Inspiration: So far, the workouts are just a long list in your profile. I have over 700 workouts, y'all. I'm not going to scroll there FOREVER.
- **Find those stupid sets** where you may have mistyped something, and fix them.
  - Inspiration: I have these stupid sets that are like 84 reps and I can't seem to find them on my own, since it's a massive headache. Why not just use a database query, right?
- **Compute a linear regression** of volume and time on a particular exercise, and see if progressive overload is being achieved.
  - Inspiration: I just wanted to see if I was on the right track on a specific workout over time.

## Technical Things

### Basics

- A workout is all the exercises you've done for a period of time.
- An exercise is a movement that targets specific muscle groups.
- A set is the sessions of work for a particular exercise.

### What You Can't Do With the API
- Delete anything.
  - You can only create or modify, except routine folders. For that, you can only make, not modify.
- Grab someone else's user's workout and copy it as a routine on your account.
  - I would love to steal someone's routine, but you can't.
- Make a new exercise template.
- Get the calculations the application just... does for you? (Like your 1RM, Most Set Volume, etc.)
  - I don't know if this is done on device, or it is already stored on the account.
  - That's why I am reverse engineering all of the PRs and milestones by hand lol and having those endpoints would honestly make my work too easy.

### Preset Hevy Muscle Groups
Since I am currently handling the muscle group table creation through for-loops, I am just compiling a list of all the muscle groups that Hevy supports.

Since Hevy can add muscle groups at any time, I will continue using the for-loops, but for speed, I might just add these values in the schema specification.
- Biceps
- Abdominals
- Cardio
- Shoulders
- Chest
- Upper Back
- Quadriceps
- Glutes
- Lower Back
- Full Body
- Forearms
- Triceps
- Calves
- Lats
- Abductors
- Adductors
  - To this day, I don't really get why they separated these two muscle groups (lol). And they are (IIRC) only used for the Hip Adductor and Abductor machines (even more lol).
- Traps
- Neck
- Other
### Hevy Workout JSON Format

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
