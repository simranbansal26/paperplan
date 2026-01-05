# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Paper Plan", layout="wide")

# --- Optional CSS for a clean sheet look ---
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; }
      div[data-testid="stDataFrame"] { border: 1px solid #e6e6e6; border-radius: 6px; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Header ---
st.markdown(
    "<div style='text-align:center; font-weight:700; font-size:22px;'>PAPER PLAN</div>",
    unsafe_allow_html=True,
)
st.write("")

c1, c2, c3, c4, c5, c6 = st.columns([0.5, 2.6, 0.5, 1.6, 0.5, 2.0])

with c1:
    st.markdown("**Subject**")
with c2:
    subject_options = ["Select", "Maths", "English", "Science", "Social Studies"]
    subject = st.selectbox(
        "",
        subject_options,
        index=subject_options.index("Select"),
        key="subject",
        label_visibility="collapsed",
    )

with c3:
    st.markdown("**Class**")
with c4:
    class_options = ["Select", 3, 4, 5, 6, 7, 8, 9, 10]
    class_val = st.selectbox(
        "",
        class_options,
        index=class_options.index("Select"),
        key="class",
        label_visibility="collapsed",
    )

with c5:
    st.markdown("**Round**")
with c6:
    round_options = ["Select", "Summer 2026", "Winter 2026", "Summer 2027"]
    round_val = st.selectbox(
        "",
        round_options,
        index=round_options.index("Select"),
        key="round",
        label_visibility="collapsed",
    )

st.write("")

# --- Session state: keep the table persistent across reruns ---
BASE_COLS = [
    "Row",
    "Question Idea",
    "Skill",
    "Sub-skill",
    "Difficulty",
    "Comment",
    "QCode",
    "QNo",
    "Status",
    "Delete",  # helper column for deleting rows
]

def make_empty_row():
    return {
        "Question Idea": "",
        "Skill": "",
        "Sub-skill": "",
        "Difficulty": "",
        "Comment": "",
        "QCode": "",
        "QNo": "",
        "Status": "",
        "Delete": False,
    }

def renumber_rows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Row"] = list(range(1, len(df) + 1))
    return df

if "paper_df" not in st.session_state:
    rows = []
    for i in range(1, 5):
        r = make_empty_row()
        r["Row"] = i
        rows.append(r)
    st.session_state.paper_df = pd.DataFrame(rows, columns=BASE_COLS)

# --- "Jump to row" via query param (used by summary hyperlinks) ---
row_param = st.query_params.get("row")
if row_param is not None:
    try:
        target = int(row_param)
        df_now = st.session_state.paper_df
        if 1 <= target <= len(df_now):
            st.info(f"Jumped to row {target}. Showing that row below.")
            st.dataframe(df_now[df_now["Row"] == target].drop(columns=["Delete"]), use_container_width=True)
        else:
            st.warning("That row number does not exist in the current table.")
    except ValueError:
        st.warning("Invalid row parameter.")

    col_clear, _ = st.columns([1, 6])
    with col_clear:
        if st.button("Clear row jump"):
            st.query_params.clear()
            st.rerun()

st.write("")

# --- Toolbar: Add / Delete ---
t1, t2, _ = st.columns([1.2, 2.2, 6])

with t1:
    if st.button("Add row"):
        df = st.session_state.paper_df.copy()
        new_r = make_empty_row()
        new_r["Row"] = len(df) + 1
        df = pd.concat([df, pd.DataFrame([new_r])], ignore_index=True)
        df = renumber_rows(df)
        st.session_state.paper_df = df
        st.rerun()

with t2:
    if st.button("Delete selected rows"):
        df = st.session_state.paper_df.copy()
        df = df[~df["Delete"]].copy()  # keep rows not marked for deletion
        if len(df) == 0:
            df = pd.DataFrame([], columns=BASE_COLS)
        df = renumber_rows(df)
        df["Delete"] = False  # reset delete flags
        st.session_state.paper_df = df
        st.query_params.clear()
        st.rerun()

# --- Main editable grid ---
difficulty_options = ["", "easy", "medium", "hard"]
status_options = ["", "Idea", "Added", "Commented", "Approved"]

df_for_editor = st.session_state.paper_df.copy()

# --- dynamic height: expand to show all rows (no internal scroll) ---
n_rows = len(df_for_editor)
ROW_PX = 35        # adjust if rows look cramped or too tall
HEADER_PX = 44
MAX_HEIGHT = 1400  # safety cap; increase if you truly want huge pages
editor_height = min(MAX_HEIGHT, HEADER_PX + (n_rows + 1) * ROW_PX)

edited_df = st.data_editor(
    st.session_state.paper_df,
    key="paper_plan_editor",
    use_container_width=True,
    num_rows="fixed",
    height = editor_height,
    hide_index=True,
    disabled=["Row"],  # keep row numbers stable and not editable
    column_config={
        "Row": st.column_config.NumberColumn(""),
        "Question Idea": st.column_config.TextColumn(width="medium"),
        "Skill": st.column_config.TextColumn(width="small"),
        "Sub-skill": st.column_config.TextColumn(width="small"),
        "Difficulty": st.column_config.SelectboxColumn(
            "Difficulty",
            options=difficulty_options,
            width="small",
        ),
        "Comment": st.column_config.TextColumn(width="small"),
        "QCode": st.column_config.TextColumn(width="small"),
        "QNo": st.column_config.TextColumn(width="small"),
        "Status": st.column_config.SelectboxColumn(
            "Status",
            options=status_options,
            width="small",
        ),
        "Delete": st.column_config.CheckboxColumn("Delete", width="small"),
    },
)

# Save edits back into session state (so edits persist)
st.session_state.paper_df = edited_df.copy()

st.write("")

# --- Difficulty summary (2 columns: Difficulty + hyperlinked row numbers) ---
df_for_summary = st.session_state.paper_df.copy()

def rows_as_links(row_nums):
    # links like: [1](?row=1), [3](?row=3)
    return ", ".join([f"[{n}](?row={n})" for n in row_nums])

summary = []
for diff in ["easy", "medium", "hard"]:
    rows_here = df_for_summary.loc[df_for_summary["Difficulty"] == diff, "Row"].tolist()
    summary.append((diff, rows_as_links(rows_here) if rows_here else ""))

# Optionally include unassigned (blank) difficulty
unassigned = df_for_summary.loc[df_for_summary["Difficulty"] == "", "Row"].tolist()
if unassigned:
    summary.append(("unassigned", rows_as_links(unassigned)))

st.markdown("### Difficulty summary")

# Render as Markdown table so hyperlinks work
md = "| Difficulty | Rows |\n|---|---|\n"
for diff, links in summary:
    md += f"| {diff} | {links} |\n"
st.markdown(md)
