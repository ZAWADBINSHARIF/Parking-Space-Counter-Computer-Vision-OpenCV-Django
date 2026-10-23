# AGENTS.md

## Project overview

This project counts free parking spaces in a video feed using classical image processing
(no machine learning) and stores parking-slot state in a Django + MySQL/MariaDB backend.
It has two parts:

1. **OpenCV scripts** (`main.py`, `ParkingSpacePicker.py`) — the desktop CV tool, now
   integrated with the backend: both scripts call `django.setup()` and read/write the
   `slots` table directly through the ORM helpers in `parking/services.py`.
2. **A Django backend** (`config/` project + `parking/` app) that keeps parking slots
   (custom name, 4-corner JSON coordinates, `open`/`booked` status) in a MySQL-compatible
   database and exposes a small JSON API for managing slots and pushing real-time status
   updates from CV results.

How the CV part works:

1. `ParkingSpacePicker.py` is the slot-management UI. It opens the reference image
   `image.png` and renders every slot stored in the database as a magenta rectangle with
   its name. Left-clicking adds a fixed-size (107x48) parking space at the clicked point
   and saves it to the database with an auto-generated name (`S1`, `S2`, ... via
   `services.next_slot_name()`); right-clicking inside a space deletes it from the
   database. Press `q` to quit.
2. `main.py` loads the slots from the database once at startup, reads `carPark.mp4` in a
   loop, preprocesses each frame (grayscale → Gaussian blur → adaptive threshold
   (inverse) → dilation), then for every slot crops its rectangle (top-left corner from
   the stored coordinates, fixed `width, height = 107, 48`) and counts non-zero pixels
   with `cv2.countNonZero`. A count below `1000` means the space is free (green
   rectangle), otherwise occupied (red rectangle). As soon as a slot's status flips,
   its row is updated in the database immediately (`services.update_slot_status`);
   unchanged slots cost no query. A `free: N/total` overlay is drawn on the frame.
3. Legacy data: the original picker stored the same fixed-size rectangles as a pickled
   list of `(x, y)` top-left corners in `CarParkingPosition`. The data migration
   `parking/migrations/0003_import_legacy_slots.py` converts those to 4-corner
   coordinates named `S1..Sn` and inserts them on `python manage.py migrate`
   (`python manage.py import_legacy_slots` re-runs the import manually).

## Repository layout

| Path                    | Purpose                                                                       |
| ----------------------- | ----------------------------------------------------------------------------- |
| `main.py`               | Runs the detection on the video feed and writes status changes to the DB.     |
| `ParkingSpacePicker.py` | Interactive tool to add/delete DB-backed slots on `image.png`.                |
| `CarParkingPosition`    | Legacy pickled `list[tuple[int, int]]` of space top-left corners (seed data). |
| `image.png`             | Reference frame (1100x720) used by the picker.                                |
| `carPark.mp4`           | Input video (~10 MB) analyzed by `main.py`; loops when finished.              |
| `manage.py`             | Django management entry point.                                                |
| `config/`               | Django project package (`settings.py`, `urls.py`); `config/__init__.py` installs the pymysql→MySQLdb shim. |
| `parking/`              | Django app: `models.py` (Slot → `slots` table), `views.py` (JSON API), `services.py` (ORM helpers), `legacy.py` (legacy-file loader/importer), `management/commands/import_legacy_slots.py`, `tests.py`. |
| `.env`                  | Database credentials (git-ignored); `.env.example` is the template.           |
| `requirements.txt`      | Pinned dependencies (CV + Django).                                            |
| `.venv/`                | Local virtual environment (git-ignored).                                      |

There is no `pyproject.toml`, no packaging, and no CI.

## Environment and dependencies

- Python 3 (the included `.venv` uses Python 3.14.7).
- Dependencies (from `requirements.txt`): `opencv-python==5.0.0.93`, `cvzone==2.0.0`,
  `numpy==2.5.1` (CV scripts) and `Django==6.1.2`, `pymysql==1.2.3`,
  `python-dotenv==1.2.4` (backend).
- Database: MariaDB (installed via Homebrew) serves as the MySQL server — Django's MySQL
  backend supports MariaDB. Django connects through pymysql, activated by
  `pymysql.install_as_MySQLdb()` in `config/__init__.py`. Connection settings come from
  `.env` (`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`), loaded with
  python-dotenv at the top of `config/settings.py`.

Setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # adjust credentials to your MySQL/MariaDB user
brew services start mariadb   # or your MySQL server
```

## Run commands

The CV scripts open GUI windows via `cv2.imshow`, so they require a display (they will
not work headless) and a reachable database (they call `django.setup()` on startup).
Run everything from the project root, since asset paths (`carPark.mp4`, `image.png`,
`CarParkingPosition`) are relative to the current working directory.

```bash
# 1. Create/upgrade the slots table and seed it from the legacy CarParkingPosition file:
python manage.py migrate
python manage.py import_legacy_slots   # optional manual re-run (idempotent)

# 2. (Optional) add/remove slots in the UI:
python ParkingSpacePicker.py           # left-click = add (auto-named S<n>), right-click = delete, q = quit

# 3. Run the counter on the video (pushes status changes to the DB):
python main.py                         # q = quit

# 4. Django backend API:
python manage.py runserver             # serves the API on http://127.0.0.1:8000
```

### JSON API (parking app)

- `GET /api/slots/` — list all slots.
- `POST /api/slots/` — create a slot: `{"name": "A1", "coordinates": [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]}`.
- `GET /api/slots/<id>/` — fetch one slot.
- `DELETE /api/slots/<id>/` — remove a slot.
- `POST /api/slots/<id>/status/` — rapid status flip: `{"status": "open"}` or `{"status": "booked"}`.
- `POST /api/slots/status/` — bulk update for a whole CV frame: `{"updates": [{"id": 1, "status": "booked"}, ...]}`;
  only rows whose status actually changed are written.

The same operations are available as ORM helpers in `parking/services.py`
(`create_slot`, `get_all_slots`, `delete_slot`, `next_slot_name`,
`update_slot_status`, `bulk_update_status`) for direct use from Python code.

## Testing

- CV scripts: verification is manual — run `main.py` and visually check that free spaces
  are outlined green, occupied ones red, and the `free: N/total` counter is correct.
- Django backend: `python manage.py test` runs `parking/tests.py` against a temporary
  `test_<DB_NAME>` database created on the MySQL/MariaDB server (the DB user therefore
  needs privileges on both the configured database and its `test_` counterpart). The
  suite covers the database connection, slot creation with 4-corner JSON coordinates,
  persistence, rapid status updates including simulated OpenCV results, slot deletion,
  auto-generated `S<n>` names, the change-only bulk-update optimization, and the
  legacy-file import (pickle + JSON). The legacy-import migration skips databases whose
  name starts with `test` so the test database starts empty.

## Code style and conventions

- CV scripts: plain procedural scripts (no classes, no `main()` guard); module-level code
  runs on import. `camelCase` for most variables and functions (e.g. `checkParkingSpace`,
  `refreshSlots`). Comments/docstrings are in English and sparse; keep it that way.
  Both scripts start with the same `DJANGO_SETTINGS_MODULE` + `django.setup()` boilerplate
  before importing anything from `parking`.
- Tunable CV constants live at the top of the scripts: the shared parking-space size
  (`width, height = 107, 48` in both CV scripts) and the free-space pixel-count
  threshold (`freePixelThreshold = 1000` in `main.py`). If the input video or camera
  angle changes, the threshold, the size, and the picked positions must be re-adjusted
  together. The same 107x48 size lives in `parking/legacy.py` (`LEGACY_WIDTH`,
  `LEGACY_HEIGHT`) for converting legacy top-left positions during import.
- Slots are stored in the DB as 4-corner JSON coordinates, but the UI always creates
  axis-aligned 107x48 boxes from the clicked top-left point; both CV scripts read the
  top-left back from `coordinates[0]` and work with the fixed size.
- New slots created in the picker are auto-named `S<n>` (one above the highest existing
  `S` number) by `services.next_slot_name()`; names are never reused or renumbered.
- Django code follows standard Django idioms (snake_case, FBVs). The table name is pinned
  with `Meta.db_table = "slots"`; coordinates are stored as a JSON list of 4 corner points
  (MariaDB represents the JSON column as LONGTEXT with a `json_valid` CHECK constraint).
- `CarParkingPosition` is binary data, not source code — do not edit it by hand. It is no
  longer written by the picker; it only serves as seed data for the legacy import.

## Security considerations

- The legacy import loads `CarParkingPosition` with `pickle.load`, which can execute
  arbitrary code. Never import a pickle file from an untrusted source; only use files
  generated locally by the original picker.
- `.env` holds the database credentials and is git-ignored — keep it out of version
  control. The shipped credentials (`parking`/`parking`) are for local development only.
- The JSON API views are `@csrf_exempt` so local tooling (curl, a CV script) can POST
  without a CSRF token; do not expose the dev server beyond localhost without
  rethinking that.
- The project has no network surface beyond the local Django dev server, no other
  secrets, and no user input beyond mouse clicks and the JSON API.
