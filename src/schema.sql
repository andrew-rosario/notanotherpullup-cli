PRAGMA foreign_keys = ON;

/*
    Workouts consist of exercises in a particular order.
    Exercises consist of sets in a particular order.
    
    Sets consist of a type, and are either weight and reps or distance and time.
    The type can either be Normal, Warmup, Failure, or Dropset.
    Weight is in kilograms. 
    Distance is in kilometres.
    It also consists of RPE (or Rate of Perceived Exertion) if enabled by the app.
*/


CREATE TABLE workouts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    update_time TEXT NOT NULL,
    creation_time TEXT NOT NULL,
);

CREATE TABLE exercises (
    workout_id TEXT,
    exercise_id INTEGER PRIMARY KEY,
    exercise_index INTEGER NOT NULL,
    exercise_title TEXT,
    exercise_notes TEXT,
    FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE
);
CREATE TABLE sets (
    exercise_id TEXT NOT NULL,
    set_id INTEGER PRIMARY KEY,
    set_index INTEGER NOT NULL,
    set_type TEXT DEFAULT 'normal',
    weight REAL,
    reps INTEGER,
    distance REAL,
    duration INTEGER,
    rpe INTEGER,
    FOREIGN KEY (exercise_id) REFERENCES exercises(workout_id) ON DELETE CASCADE
);

