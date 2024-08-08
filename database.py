import sqlite3
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

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
    days_in_future = random.randint(1, 120)  # Random number of days between 1 and 30
    hours_in_future = random.randint(0, 23)  # Random number of hours between 0 and 23
    minutes_in_future = random.randint(
        0, 59
    )  # Random number of minutes between 0 and 59
    future_datetime = now + timedelta(
        days=days_in_future, hours=hours_in_future, minutes=minutes_in_future
    )
    return future_datetime.strftime("%Y-%m-%d %H:%M:%S")


def generate_task():
    tasks = [
        "House Cleaning",
        "Regular Cleaning",
        "Deep Cleaning",
        "Laundry Service",
        "Plumbing Service",
        "Electrical Service",
        "Gardening Service",
    ]
    return random.choice(tasks)


def generate_name():
    names = [
        "John Doe",
        "Jane Doe",
        "Alice",
        "Bob",
        "Charlie",
        "David",
        "Eve",
        "Frank",
        "Grace",
        "Heidi",
    ]
    return random.choice(names)


employees = [
    (
        generate_name(),
        generate_task(),
        random.randint(1, 10),
        generate_future_datetime(),
        random.randint(50, 300),
    )
    for i in range(50)
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
    user_id TEXT NOT NULL,
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
