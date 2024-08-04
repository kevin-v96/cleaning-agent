import sqlite3

conn = sqlite3.connect("availabilities.sqlite")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS availabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    service TEXT NOT NULL,
    service_length INTEGER,
    next_availability DATETIME NOT NULL)"""
)

employees = [
    ("John Doe", "House Cleaning", 3, "2024-08-01 08:00:00"),
    ("Jane Doe", "Apartment Cleaning", 4, "2024-08-03 14:00:00"),
    ("John Doe", "Plumbing", 3, "2024-08-01 08:00:00"),
    ("Jane Doe", "Post-renovation Cleaning", 4, "2024-08-03 14:00:00"),
    ("John Doe", "Holiday Cleaning", 3, "2024-08-01 08:00:00"),
    ("Jane Doe", "Coloring", 4, "2024-08-03 14:00:00"),
    ("John Doe", "AC Repair", 3, "2024-08-01 08:00:00"),
    ("Jane Doe", "Wallpaper", 4, "2024-08-03 14:00:00"),
]

# Insert data into the 'employee' table
insert_query = "INSERT INTO availabilities (name, service, service_length, next_availability) VALUES (?, ?, ?, ?);"
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
    required_date DATETIME
    service_length_required INTEGER)"""
)

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Table created and data inserted successfully.")
