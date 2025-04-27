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

def move_task(tasks, bucket, idx, direction):
    indices = [i for i, task in enumerate(tasks) if task["bucket"] == bucket]
    current_pos = indices[idx]

    if direction == "up" and idx > 0:
        swap_pos = indices[idx - 1]
        tasks[current_pos], tasks[swap_pos] = tasks[swap_pos], tasks[current_pos]
    elif direction == "down" and idx < len(indices) - 1:
        swap_pos = indices[idx + 1]
        tasks[current_pos], tasks[swap_pos] = tasks[swap_pos], tasks[current_pos]

    save_tasks(tasks)

# --- App Layout
st.set_page_config(page_title="GoalBuckets", layout="wide")

st.title("GoalBuckets: Daily Dashboard")
quote = pick_quote()
st.info(f"{quote}")

# --- Load Today's Tasks
tasks = load_tasks()

# --- Add New Task
with st.expander("Add New Task", expanded=False):
    new_task = st.text_input("Task Name")
    bucket_choice = st.selectbox("Assign to Bucket", BUCKETS)
    if st.button("Add Task"):
        if new_task.strip() != "":
            tasks.append({"task": new_task.strip(), "bucket": bucket_choice, "completed": False})
            save_tasks(tasks)
            st.rerun()

st.divider()

# --- Show Buckets
cols = st.columns(5)

for idx, bucket in enumerate(BUCKETS):
    with cols[idx % 5]:
        st.subheader(bucket)
        bucket_tasks = [task for task in tasks if task["bucket"] == bucket]

        for i, task in enumerate(bucket_tasks):
            col1, col2, col3 = st.columns([1, 5, 1])

            with col1:
                if st.button("↑", key=f"up-{bucket}-{i}"):
                    move_task(tasks, bucket, i, "up")
                    st.rerun()
                if st.button("↓", key=f"down-{bucket}-{i}"):
                    move_task(tasks, bucket, i, "down")
                    st.rerun()

            with col2:
                task_done = st.checkbox(task["task"], value=task["completed"], key=f"{bucket}-{i}")
                index_in_tasks = tasks.index(task)
                tasks[index_in_tasks]["completed"] = task_done

save_tasks(tasks)

# --- Holding Tank
with st.expander("Holding Tank (Unfinished tasks from before)", expanded=False):
    holding_tasks = [task for task in tasks if task["bucket"] == "Holding Tank"]
    for i, task in enumerate(holding_tasks):
        col1, col2, col3 = st.columns([1, 5, 1])

        with col2:
            task_done = st.checkbox(task["task"], value=task["completed"], key=f"holding-{i}")
            index_in_tasks = tasks.index(task)
            tasks[index_in_tasks]["completed"] = task_done

save_tasks(tasks)

# --- Daily Progress Dashboard
st.divider()
st.header("Daily Progress")

df = pd.DataFrame(tasks)
if not df.empty:
    progress = df.groupby("bucket")["completed"].mean().fillna(0) * 100
    st.bar_chart(progress)
else:
    st.write("No tasks yet today.")

# --- Historical Trends
st.divider()
st.header("Trends Over Time")

all_tasks = []
for filename in os.listdir("tasks"):
    if filename.endswith(".json"):
        filepath = os.path.join("tasks", filename)
        with open(filepath, "r") as f:
            day_tasks = json.load(f)
            task_date = filename.replace(".json", "")
            for task in day_tasks:
                all_tasks.append({
                    "date": task_date,
                    "bucket": task["bucket"],
                    "completed": task["completed"]
                })

if all_tasks:
    history_df = pd.DataFrame(all_tasks)
    history_df["date"] = pd.to_datetime(history_df["date"])
    history_df = history_df.sort_values("date")

    option = st.selectbox("View progress by:", ["Day", "Week", "Month", "Year"])

    if option == "Day":
        trend = history_df.groupby(["date", "bucket"])["completed"].mean().reset_index()
        trend["completed"] *= 100
        for bucket in BUCKETS:
            bucket_data = trend[trend["bucket"] == bucket]
            if not bucket_data.empty:
                st.line_chart(bucket_data.set_index("date")["completed"], height=200)
    elif option == "Week":
        history_df["week"] = history_df["date"].dt.to_period('W').apply(lambda r: r.start_time)
        trend = history_df.groupby(["week", "bucket"])["completed"].mean().reset_index()
        trend["completed"] *= 100
        for bucket in BUCKETS:
            bucket_data = trend[trend["bucket"] == bucket]
            if not bucket_data.empty:
                st.line_chart(bucket_data.set_index("week")["completed"], height=200)
    elif option == "Month":
        history_df["month"] = history_df["date"].dt.to_period('M').apply(lambda r: r.start_time)
        trend = history_df.groupby(["month", "bucket"])["completed"].mean().reset_index()
        trend["completed"] *= 100
        for bucket in BUCKETS:
            bucket_data = trend[trend["bucket"] == bucket]
            if not bucket_data.empty:
                st.line_chart(bucket_data.set_index("month")["completed"], height=200)
    elif option == "Year":
        history_df["year"] = history_df["date"].dt.year
        trend = history_df.groupby(["year", "bucket"])["completed"].mean().reset_index()
        trend["completed"] *= 100
        for bucket in BUCKETS:
            bucket_data = trend[trend["bucket"] == bucket]
            if not bucket_data.empty:
                st.line_chart(bucket_data.set_index("year")["completed"], height=200)
else:
    st.write("Not enough historical data yet.")
