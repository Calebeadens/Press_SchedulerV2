import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# ---------------------- Config & Setup ----------------------

st.set_page_config(layout="wide")
st.title("📅 Printing Press Scheduler")

# Static product rates dictionary
product_rates = {
    'DUT10-40360R6W': 4.76,
    'DUT9-40330R6W': 4.76,
    'DUT9-40360R6W': 4.76,
    'U10-30331RCA6W': 5.41,
    'U10-30333RCA5W': 5.95,
    'U10-30333RCA6W': 5.95,
    'U10-40386R5WTG': 5.95,
    'U9-20346R6W': 5.71,
    'S12-30331RCA6W': 4.33,
    'SX12-20346R6W': 4.33,
    'SX12-30444D6W': 5.49,
    'SX12-40360R6W': 4.37,
    'SX20-20346R5W': 5.22,
    'SX20-30331R5W': 5.22,
    'SX20-30331RCA5W': 5.22,
    'SX20-30444D5W': 5.27,
    'U9-30331R5W': 5.19,
    'U9-30331RCA5W': 5.50
}

# Raw board widths to determine press
board_widths = {
    'B163600316C': 60.3125,
    'B163510332C': 51.5,
    'B206600316C': 60.3125,
    'B206500708C': 50.875,
    'B196510332C': 51.5,
    'B166420332C': 42.5,
    'B206420332C': 42.5,
    'B206420508C': 50.875,
    'B196420508C': 50.875
}

# ---------------------- Data & State ----------------------

if 'jobs' not in st.session_state:
    st.session_state.jobs = []

if 'suggestions' not in st.session_state:
    st.session_state.suggestions = []

if 'maintenance' not in st.session_state:
    st.session_state.maintenance = []

# ---------------------- Sidebar Inputs ----------------------

st.sidebar.header("➕ Add New Job")
product = st.sidebar.selectbox("Product Number", list(product_rates.keys()))
raw_board = st.sidebar.text_input("Raw Board Number")
rolls = st.sidebar.number_input("Roll Quantity", min_value=1)
run_by = st.sidebar.date_input("Run By Date", value=datetime.today())

preferred_start = st.sidebar.time_input("Preferred Start Time (optional)", value=None)

if st.sidebar.button("Add Job"):
    rate = product_rates[product]
    board_width = board_widths.get(raw_board, 50.0)
    press = "Heidelberg" if board_width > 50 else "Kidder"
    job = {
        'Product': product,
        'RawBoard': raw_board,
        'Rolls': rolls,
        'Rate': rate,
        'BoardWidth': board_width,
        'RunBy': run_by,
        'PreferredStart': preferred_start,
        'Press': press
    }
    st.session_state.jobs.append(job)
    st.success("✅ Job added to schedule")

# ---------------------- Maintenance Entry ----------------------

st.sidebar.header("🔧 Maintenance")
maint_date = st.sidebar.date_input("Maintenance Date", value=datetime.today())
maint_start = st.sidebar.time_input("Start Time")
maint_end = st.sidebar.time_input("End Time")
press_choice = st.sidebar.selectbox("Press", ["Heidelberg", "Kidder"])

if st.sidebar.button("Add Maintenance"):
    st.session_state.maintenance.append({
        "Press": press_choice,
        "Start": datetime.combine(maint_date, maint_start),
        "End": datetime.combine(maint_date, maint_end)
    })
    st.success("🛠️ Maintenance scheduled")

# ---------------------- Chat & Suggestions ----------------------

st.sidebar.header("💬 Chat / Suggestions")
chat_input = st.sidebar.text_input("Type something...")
if st.sidebar.button("Send"):
    if chat_input.lower().startswith("suggest:"):
        st.session_state.suggestions.append(chat_input[8:].strip())
        st.success("💡 Suggestion recorded.")
    else:
        st.warning("Please prefix suggestions with 'suggest:'")

# ---------------------- Scheduler ----------------------

def schedule_jobs(jobs, maintenance):
    df = pd.DataFrame(jobs)
    df["DurationHours"] = df["Rolls"] / df["Rate"]
    df["Start"] = None
    df["End"] = None

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    press_avail = {"Heidelberg": now, "Kidder": now}

    for i, row in df.iterrows():
        start_time = datetime.combine(row["RunBy"], row["PreferredStart"]) if row["PreferredStart"] else press_avail[row["Press"]]
        end_time = start_time + timedelta(hours=row["DurationHours"])
        df.at[i, "Start"] = start_time
        df.at[i, "End"] = end_time
        press_avail[row["Press"]] = end_time

    return df

scheduled_df = schedule_jobs(st.session_state.jobs, st.session_state.maintenance)

# ---------------------- Gantt View ----------------------

st.subheader("📊 Job Schedule")

if not scheduled_df.empty:
    fig = px.timeline(
        scheduled_df,
        x_start="Start",
        x_end="End",
        y="Press",
        color="Product",
        title="Gantt Chart - Jobs per Press"
    )
    fig.update_yaxes(categoryorder="category descending")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No jobs scheduled yet.")

# ---------------------- Suggestions Display ----------------------

if st.session_state.suggestions:
    st.subheader("💡 Suggestions")
    for s in st.session_state.suggestions:
        st.write(f"- {s}")
