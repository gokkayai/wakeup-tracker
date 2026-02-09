import streamlit as st
import requests
import pandas as pd

API_BASE = "http://127.0.0.1:5000"

st.set_page_config(page_title="Wake-up Tracker", layout="wide")
st.title("Wake-up Tracker")


def request_data(endpoint):
    try:
        r = requests.get(f"{API_BASE}{endpoint}")
        if r.status_code == 200:
            return r.json()
        st.error(f"Error {r.status_code}: {r.json().get('error', 'Unknown error')}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the API. Is the Flask server running?")
        return []


option = st.sidebar.selectbox(
    "Choose action:",
    (
        "Show all wake-ups",
        "Add wake-up",
        "Update wake-up",
        "Delete wake-up",
        "Streak stats",
    ),
)

if option == "Show all wake-ups":
    st.subheader("All entries")
    col1, col2 = st.columns(2)
    with col1:
        day_from = st.text_input("From (YYYY-MM-DD)", "")
    with col2:
        day_to = st.text_input("To (YYYY-MM-DD)", "")

    endpoint = "/wakeups"
    params = []
    if day_from:
        params.append(f"from={day_from}")
    if day_to:
        params.append(f"to={day_to}")
    if params:
        endpoint += "?" + "&".join(params)

    data = request_data(endpoint)
    if data:
        st.dataframe(pd.DataFrame(data), use_container_width=True)

elif option == "Add wake-up":
    st.subheader("Add entry")
    day = st.text_input("Day (YYYY-MM-DD)")
    wake_time = st.text_input("Wake time (HH:MM)")
    sleep_time = st.text_input("Sleep time (optional, HH:MM)", "")
    note = st.text_input("Note (optional)", "")

    if st.button("Create"):
        payload = {"day": day, "wake_time": wake_time, "sleep_time": sleep_time, "note": note}
        try:
            r = requests.post(f"{API_BASE}/wakeups", json=payload)
            if r.status_code == 201:
                st.success("Created.")
                st.json(r.json())
            else:
                st.error(f"Error {r.status_code}: {r.json().get('error', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API.")

elif option == "Update wake-up":
    st.subheader("Update entry")
    day = st.text_input("Day to update (YYYY-MM-DD)")

    set_wake = st.checkbox("Update wake time")
    wake_time = st.text_input("Wake time (HH:MM)", "")

    set_sleep = st.checkbox("Update sleep time (can be empty)")
    sleep_time = st.text_input("Sleep time (HH:MM or empty)", "")

    set_note = st.checkbox("Update note (can be empty)")
    note = st.text_input("Note (text or empty)", "")

    if st.button("Update"):
        payload = {}
        if set_wake:
            payload["wake_time"] = wake_time
        if set_sleep:
            payload["sleep_time"] = sleep_time  # empty string clears it
        if set_note:
            payload["note"] = note  # empty string clears it

        try:
            r = requests.put(f"{API_BASE}/wakeups/{day}", json=payload)
            if r.status_code == 200:
                st.success("Updated.")
                st.json(r.json())
            else:
                st.error(f"Error {r.status_code}: {r.json().get('error', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API.")

elif option == "Delete wake-up":
    st.subheader("Delete entry")
    day = st.text_input("Day to delete (YYYY-MM-DD)")

    if st.button("Delete"):
        try:
            r = requests.delete(f"{API_BASE}/wakeups/{day}")
            if r.status_code == 200:
                st.success("Deleted.")
            else:
                st.error(f"Error {r.status_code}: {r.json().get('error', 'Unknown error')}")
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API.")

elif option == "Streak stats":
    st.subheader("Streak stats")
    col1, col2 = st.columns(2)
    with col1:
        target_time = st.text_input("Target time (HH:MM)", "07:00")
    with col2:
        tolerance_min = st.text_input("Tolerance minutes", "10")

    if st.button("Compute"):
        data = request_data(f"/streak?target_time={target_time}&tolerance_min={tolerance_min}")
        if data:
            st.json(data)
