import sqlite3

conn = sqlite3.connect("availabilities.db")
cursor = conn.cursor()

cursor.execute(
    """CREATE TABLE IF NOT EXISTS availabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    service TEXT NOT NULL,
    next_availability DATETIME NOT NULL)"""
)

employees = [
    ("John Doe", "House Cleaning", "2024-08-01 08:00:00"),
    ("Jane Doe", "Apartment Cleaning", "2024-08-03 14:00:00"),
    ("John Smith", "Plumbing", "2024-08-04 08:00:00"),
]

# Insert data into the 'employee' table
insert_query = (
    "INSERT INTO availabilities (name, service, next_availability) VALUES (?, ?, ?);"
)
cursor.executemany(insert_query, employees)

print(cursor.execute("SELECT * FROM availabilities").fetchall())

# Commit the changes
conn.commit()

# Close the connection
conn.close()

print("Table created and data inserted successfully.")
