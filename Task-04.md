Task 4: Dynamic Slot Management, Data Migration & Real-Time Status Updates

Objective

Implement dynamic slot management via the UI, migrate legacy JSON slot data to the MySQL database, and establish real-time status updates (Occupied/Open) using OpenCV image processing integrated with the Django backend.

Requirements

1. Legacy Data Migration (JSON to Database)

Read existing parking slot bounding box coordinates and identifiers currently stored in the JSON file.

Insert all existing JSON slot entries into the MySQL slots table through Django ORM upon initial setup/migration.

2. Dynamic UI Slot Selection & Modification

Add Slot: When a user selects and draws a four-corner bounding box for a parking slot on the camera feed/image and assigns a slot name, automatically create and save the entry into the MySQL database (slots table).

Remove Slot: If a user unselects/deletes a slot from the UI, immediately remove the corresponding record from the database.

Display Existing Slots: Fetch and render all saved slots from the database onto the image overlay dynamically so users can modify, delete, or add slots on top of existing configurations.

3. Real-Time Occupancy Detection & Database Updates (OpenCV Integration)

Process video/image frames using OpenCV to evaluate each slot defined in the database.

Car Detected (Occupied): When a vehicle enters a slot area, immediately update the status field in the database to indicate the slot is blocked/occupied (e.g., status = "booked" or "occupied").

Car Departed (Vacant): When the vehicle leaves the slot, quickly reflect the change in the database to indicate the slot is vacant/open (e.g., status = "open").

Ensure DB updates are lightweight and optimized for high-frequency video frame processing.