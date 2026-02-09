# Wake-up Tracker
A simple local habit-tracking application for logging daily wake-up times and computing goal-based streak statistics.
Built with Flask, SQLite, and Streamlit.

## Features

- Log daily wake-up times (and optional sleep time and notes)

- Store data locally using SQLite

- REST API for CRUD operations

- Goal-based streak calculation with tolerance

- Streamlit UI for viewing and editing entries

- Unit tests for streak logic

## Setup and Running The Application
Install dependencies:
```bash
pip install -r requirements.txt
```
Start the API (Terminal 1):
```bash
python api.py
```
On first run, the SQLite database (wakeups.db) is created automatically.

Start the Streamlit frontend (Terminal 2):
```bash
streamlit run app.py
```
Open the browser URL shown by Streamlit to use the app.