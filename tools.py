# langchain
from langchain_core.tools import tool

# db
import sqlite3

from typing import Optional, Union
from datetime import datetime, date

availabilities_db = "availabilities.sqlite"
bookings_db = "bookings.sqlite"


@tool
def check_availability(
    service_required: str = "House Cleaning",
    service_length: Optional[int] = None,
) -> list[dict]:
    """
    Search for the next availability for the kind of cleaning service required.

    Args:
        service_required (str): The kind of cleaning service required. Defaults to House Cleaning.
        service_length (Optional[int]): The length of the service offered. Defaults to None.

    Returns:
        list[dict]: A list of next availabilities for the type of cleaning service required by the user.
    """
    conn = sqlite3.connect(availabilities_db)
    cursor = conn.cursor()

    query = "SELECT * FROM availabilities WHERE service LIKE ?"
    params = []
    params.append(f"%{service_required}%")

    if service_length:
        query += " AND service_length LIKE ?"
        params.append(f"%{service_length}%")

    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]


@tool
def book_service(
    user_id: int,
    worker_id: int,
    service_required: Optional[str] = "House Cleaning",
    required_date: Optional[Union[datetime, date]] = None,
    service_length_required: Optional[int] = None,
) -> str:
    """
    Book a service for a particular customer.

    Args:
        user_id (int): The ID of the user who is making a booking.
        worker_id (int): The ID of the worker whose service is required.
        service_required (Optional[str]): The kind of service required by the user. Defaults to House Cleaning.
        required_date (Optional[Union[datetime, date]]): The date and time when the service is required. Defaults to None.
        service_length_required (Optional[int]): The length of time for which the service is required.

    Returns:
        str: A message indicating whether the service information was successfully updated or not.
    """
    conn = sqlite3.connect(bookings_db)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO bookings (user_id, worker_id, service_required, required_date, service_length_required) VALUES (?, ?, ?, ?, ?);",
        (user_id, worker_id, service_required, required_date, service_length_required),
    )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Added booking for user {user_id} with worker {worker_id} for {required_date} successfully updated."
    else:
        conn.close()
        return f"No record found for worker with ID {worker_id}."


@tool
def cancel_booking(booking_id: int) -> str:
    """
    Cancel a home service booking by its ID.

    Args:
        booking_id (int): The ID of the booking to cancel.

    Returns:
        str: A message indicating whether the booking was successfully cancelled or not.
    """
    conn = sqlite3.connect(bookings_db)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Booking {booking_id} successfully cancelled."
    else:
        conn.close()
        return f"No booking found with ID {booking_id}."
