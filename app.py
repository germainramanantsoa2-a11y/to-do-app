import streamlit as st
import json
import os
import hashlib
from datetime import datetime, timedelta

TASKS_FILE = "tasks.json"
USERS_FILE = "users.json"

DEFAULT_USERS = {
    "personnel": {"password": hashlib.sha256("1234".encode()).hexdigest(), "role": "personnel", "name": "Personnel"},
    "patron": {"password": hashlib.sha256("admin".encode()).hexdigest(), "role": "patron", "name": "Patron"}
}

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    with open(USERS_FILE, "w") as f:
        json.dump(DEFAULT_USERS, f, indent=2)
    return DEFAULT_USERS

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

def load_tasks():
    if os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    return []

def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=2)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def login_page(users):
    st.title("🔐 Connexion")
    username = st.text_input("Utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username in users:
            if users[username]["password"] == hash_password(password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = users[username]["role"]
                st.session_state.name = users[username]["name"]
                st.rerun()
            else:
                st.error("Mot de passe incorrect")
        else:
            st.error("Utilisateur inconnu")

def change_password(users):
    st.subheader("🔑 Changer le mot de passe")
    old_pwd = st.text_input("Ancien mot de passe", type="password", key="old")
    new_pwd = st.text_input("Nouveau mot de passe", type="password", key="new")
    confirm_pwd = st.text_input("Confirmer le mot de passe", type="password", key="confirm")

    if st.button("Valider"):
        username = st.session_state.username
        if users[username]["password"]!= hash_password(old_pwd):
            st.error("Ancien mot de passe incorrect")
        elif new_pwd!= confirm_pwd:
            st.error("Les mots de passe ne correspondent pas")
        elif len(new_pwd) < 4:
            st.error("Mot de passe trop court, min 4 caractères")
        else:
            users[username]["password"] = hash_password(new_pwd)
            save_users(users)
            st.success("Mot de passe changé!")
            st.rerun()

def get_status(validated_me, validated_boss):
    if validated_me and validated_boss:
        return "Validé", "green"
    elif validated_me and not validated_boss:
        return "En attente toi", "orange"
    elif validated_boss and not validated_me:
        return "En attente patron", "orange"
    return "À faire", "red"

def get_next_due_date(period, frequency):
    try:
        if frequency == "Jour":
            return (datetime.now() + timedelta(days=1)).strftime("%d/%m")
        elif frequency == "Semaine":
            return (datetime.now() + timedelta(weeks=1)).strftime("Semaine %W")
        elif frequency == "Mois":
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            return next_month.strftime("%B %Y")
        elif frequency == "Trimestre":
            month = datetime.now().month
            quarter = (month - 1) // 3 + 1
            next_quarter = quarter % 4 + 1
            year = datetime.now().year if quarter!= 4 else datetime.now().year + 1
            return f"T{next_quarter} {year}"
    except:
        return period
    return period

st.set_page_config(page_title="Suivi Tâches", layout="wide")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

users = load_users()

if not st.session_state.logged_in:
    login_page(users)
    st.stop()

# Sidebar
st.sidebar.write(f"Connecté en tant que: **{st.session_state.name}**")
if st.sidebar.button("Déconnexion"):
    st.session_state.logged_in = False
    st.rerun()

with st.sidebar.expander("Changer le mot de passe"):
    change_password(users)

if "tasks" not in st.session_state:
    st.session_state.tasks = load_tasks()

st.title(f"📋 Suivi Tâches - {st.session_state.name}")

if st.session_state.role == "patron":
    with st.form("add_task"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nom de la tâche")
            batch = st.text_input("Lot / Batch", placeholder="Optionnel")
            frequency = st.selectbox("Fréquence", ["Jour", "Semaine", "Mois", "Trimestre"])
        with col2:
            period = st.text_input("Période", placeholder="ex: 22/05, Semaine 21, Mai, T2")

        submitted = st.form_submit_button("Ajouter")
        if submitted and name:
            new_task = {
                "name": name,
                "batch": batch,
                "frequency": frequency,
                "period": period,
                "validated_by_me": False,
                "validated_by_boss": False,
                "cache_date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.tasks.append(new_task)
            save_tasks(st.session_state.tasks)
            st.rerun()

st.divider()

overdue = sum(1 for t in st.session_state.tasks
              if not (t["validated_by_me"] and t["validated_by_boss"]))
st.metric("Tâches en attente", overdue)

for i, t in enumerate(st.session_state.tasks):
    status, color = get_status(t["validated_by_me"], t["validated_by_boss"])
    next_due = get_next_due_date(t["period"], t["frequency"])

    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])

        with col1:
            st.markdown(f"### {t['name']}")
            batch_info = f" | **Lot:** {t['batch']}" if t['batch'] else ""
            st.write(f"**Fréquence:** {t['frequency']} - {t['period']}{batch_info}")
            st.write(f"**Prochaine échéance:** {next_due}")
            st.caption(f"Dernière maj: {t['cache_date']}")

        with col2:
            if st.session_state.role == "personnel":
                me = st.checkbox("Validé par moi", value=t["validated_by_me"], key=f"me{i}")
                st.checkbox("Validé par patron", value=t["validated_by_boss"], key=f"boss{i}", disabled=True)
                if me!= t["validated_by_me"]:
                    st.session_state.tasks[i]["validated_by_me"] = me
                    st.session_state.tasks[i]["cache_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            elif st.session_state.role == "patron":
                st.checkbox("Validé par moi", value=t["validated_by_me"], key=f"me{i}", disabled=True)
                boss = st.checkbox("Validé par patron", value=t["validated_by_boss"], key=f"boss{i}")
                if boss!= t["validated_by_boss"]:
                    st.session_state.tasks[i]["validated_by_boss"] = boss
                    st.session_state.tasks[i]["cache_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_tasks(st.session_state.tasks)
                    st.rerun()

            st.markdown(f"<span style='color:{color}; font-weight:bold;'>● {status}</span>", unsafe_allow_html=True)

        with col3:
            if st.session_state.role == "patron":
                if st.button("Supprimer", key=f"del{i}"):
                    st.session_state.tasks.pop(i)
                    save_tasks(st.session_state.tasks)
                    st.from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, ton app To-do marche !"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
