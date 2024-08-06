import sqlite3
import random
from datetime import datetime, timedelta

conn = sqlite3.connect("availabilities.sqlite")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS availabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    service TEXT NOT NULL,
    service_length INTEGER NOT NULL,
    next_availability DATETIME NOT NULL,
    price INTEGER NOT NULL)"""
)


# Function to generate a random future datetime
def generate_future_datetime():
    now = datetime.now()
    days_in_future = random.randint(1, 30)  # Random number of days between 1 and 30
    hours_in_future = random.randint(0, 23)  # Random number of hours between 0 and 23
    minutes_in_future = random.randint(
        0, 59
    )  # Random number of minutes between 0 and 59
    future_datetime = now + timedelta(
        days=days_in_future, hours=hours_in_future, minutes=minutes_in_future
    )
    return future_datetime.strftime("%Y-%m-%d %H:%M:%S")


employees = [
    ("John Doe", "House Cleaning", 3, generate_future_datetime(), 100),
    ("Jane Doe", "Regular Cleaning", 4, generate_future_datetime(), 125),
    ("John Doe", "House Cleaning", 3, generate_future_datetime(), 95),
    ("Jane Doe", "Regular Cleaning", 4, generate_future_datetime(), 75),
    ("John Doe", "House Cleaning", 3, generate_future_datetime(), 105),
    ("Jane Doe", "Regular Cleaning", 4, generate_future_datetime(), 98),
    ("John Doe", "House Cleaning", 3, generate_future_datetime(), 30),
    ("Jane Doe", "Regular Cleaning", 4, generate_future_datetime(), 125),
]

# Insert data into the 'employee' table
insert_query = "INSERT INTO availabilities (name, service, service_length, next_availability, price) VALUES (?, ?, ?, ?, ?);"
cursor.executemany(insert_query, employees)

print(cursor.execute("SELECT * FROM availabilities").fetchall())

# Commit the changes
conn.commit()

# Close the connection
conn.close()

# bookings table
conn = sqlite3.connect("bookings.sqlite")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    worker_id INTEGER NOT NULL,
    service_required TEXT NOT NULL,
    required_date DATETIME,
    service_length_required INTEGER)"""
)

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Table created and data inserted successfully.")
