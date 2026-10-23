Task 2: Slot Table Design and ORM/API Integration

Objective

Create the database migration and model specifically for the slots table based on the provided database design PDF link/reference, and set up logic to save and update slot states.

Database Schema Reference (slots table only)

Table Name: slots

Fields:

id (int, Primary Key)

name (varchar, for custom slot name/number e.g., "A1")

coordinates (json, to store the 4-corner bounding box coordinates generated from UI clicks)

status (varchar, to quickly update whether the slot is booked/occupied or open)

Requirements

Model Definition:

Define the Slot model in models.py matching the exact schema above.

Run migrations to create the slots table in the MySQL database.

Data Insertion & Real-time Update Logic:

Provide views/APIs/ORM functions to:

Insert a new slot with its custom name and JSON coordinates when created from the frontend UI.

Rapidly update the status field (e.g., "open" or "booked") based on OpenCV image processing results.