import streamlit as st
import pandas as pd
import json
import os
import random
from datetime import date, timedelta

# --- Load settings
with open("settings.json", "r") as f:
    settings = json.load(f)

BUCKETS = settings["buckets"]
RECURRING_TASKS = settings["recurring_tasks"]

# --- Load quotes
with open("quotes.json", "r") as f:
    QUOTES = json.load(f)

# --- Helper Functions
def get_today_file():
    today = date.today().isoformat()
    return f"tasks/{today}.json"

def load_tasks():
    if not os.path.exists("tasks"):
        os.makedirs("tasks")
    today_file = get_today_file()

    if os.path.exists(today_file):
        with open(today_file, "r") as f:
            return json.load(f)
    else:
        # Create today's file
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        yesterday_file = f"tasks/{yesterday}.json"
        tasks = []

        if os.path.exists(yesterday_file):
            with open(yesterday_file, "r") as f:
                old_tasks = json.load(f)
                for task in old_tasks:
                    if not task["completed"]:
                        task["bucket"] = "Holding Tank"
                        tasks.append(task)

        # Add recurring tasks
        for rtask in RECURRING_TASKS:
            tasks.append({
                "task": rtask["task"],
                "bucket": rtask["bucket"],
                "completed": False
            })

        save_tasks(tasks)
        return tasks

def save_tasks(tasks):
    today_file = get_today_file()
    with open(today_file, "w") as f:
        json.dump(tasks, f, indent=2)

def pick_quote():
    return random.choice(QUOTES)

# --- App Layout
st.set_page_config(page_title="GoalBuckets", layout="wide")

st.title("🌟 GoalBuckets: Daily Dashboard")
quote = pick_quote()
st.info(f"_{quote}_")

# --- Load Today's Tasks
tasks = load_tasks()

# --- Add New Task
with st.expander("➕ Add New Task"):
    new_task = st.text_input("Task Name")
    bucket_choice = st.selectbox("Assign to Bucket", BUCKETS)
    if st.button("Add Task"):
        if new_task.strip() != "":
            tasks.append({"task": new_task.strip(), "bucket": bucket_choice, "completed": False})
            save_tasks(tasks)
            st.success("Task Added!")

st.markdown("---")

# --- Show Buckets
cols = st.columns(5)

for idx, bucket in enumerate(BUCKETS):
    with cols[idx % 5]:
        st.subheader(bucket)
        for i, task in enumerate(tasks):
            if task["bucket"] == bucket:
                task_done = st.checkbox(task["task"], value=task["completed"], key=f"{bucket}-{i}")
                tasks[i]["completed"] = task_done

save_tasks(tasks)

# --- Holding Tank
with st.expander("🔄 Holding Tank (Unfinished tasks from before)"):
    for i, task in enumerate(tasks):
        if task["bucket"] == "Holding Tank":
            task_done = st.checkbox(task["task"], value=task["completed"], key=f"holding-{i}")
            tasks[i]["completed"] = task_done

save_tasks(tasks)

# --- Dashboard
st.markdown("---")
st.header("📈 Daily Progress")

df = pd.DataFrame(tasks)
if not df.empty:
    progress = df.groupby("bucket")["completed"].mean().fillna(0) * 100
    st.bar_chart(progress)
else:
    st.write("No tasks yet today.")
