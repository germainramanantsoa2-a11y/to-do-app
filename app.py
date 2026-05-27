import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta

USERS_FILE = "users.json"
TASKS_FILE = "tasks.json"

DEFAULT_USERS = {
    "Germain": {"password": hashlib.sha256("1234".encode()).hexdigest(), "role": "personnel", "name": "Germain"},
    "patron": {"password": hashlib.sha256("admin".encode()).hexdigest(), "role": "patron", "name": "Patron"}
}

# Sur Render gratuit, on garde tout en session state pour éviter les pertes
def load_users():
    if "users" not in st.session_state:
        st.session_state.users = DEFAULT_USERS
    return st.session_state.users

def save_users(users):
    st.session_state.users = users
    # Essaie d’écrire quand même, mais ça va sauter au redéploiement
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except:
        pass

def load_tasks():
    if "tasks" not in st.session_state:
        st.session_state.tasks = []
    return st.session_state.tasks

def save_tasks(tasks):
    st.session_state.tasks = tasks
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    except:
        pass
