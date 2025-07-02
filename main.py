import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import date, timedelta

# === Streamlit page ===
st.set_page_config(page_title="📊 Jira Sprint Effort Dashboard", layout="wide")
st.title("📊 Jira Sprint Effort Breakdown")

# === Inputs ===
st.sidebar.header("🔑 Jira API Config")
JIRA_URL = st.sidebar.text_input("Jira URL", "https://kpisoft.atlassian.net/")
EMAIL = st.sidebar.text_input("Email", "swaraj.s@entomo.co")
API_TOKEN = st.sidebar.text_input("API Token", type="password")

today = date.today()
one_month_ago = today - timedelta(days=30)

st.sidebar.header("📅 Sprint & Date Ranges")
SPRINT_ID = st.sidebar.text_input("Sprint ID", "722")

bugfix_start = st.sidebar.date_input("Bug Fixing Start Date", one_month_ago)
bugfix_end = st.sidebar.date_input("Bug Fixing End Date", today)
regression_start = st.sidebar.date_input("Regression Start Date", one_month_ago)
regression_end = st.sidebar.date_input("Regression End Date", today)
dev_start = st.sidebar.date_input("DEV Start Date", one_month_ago)
dev_end = st.sidebar.date_input("DEV End Date", today)
ps_start = st.sidebar.date_input("PS Start Date", one_month_ago)
ps_end = st.sidebar.date_input("PS End Date", today)

if st.sidebar.button("🚀 Run Effort Breakdown"):

    resource_static = [
        {"Name": "Abhishek Patro", "Target SP": None, "Senior Dev": "No"},
        {"Name": "Amit Krishna", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Avinash S", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Chaithra B", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "chandan k", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Dhaarani Devi", "Target SP": None, "Senior Dev": "No"},
        {"Name": "Gangadhara S M", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Harish Ramakrishna", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Krishna S", "Target SP": None, "Senior Dev": "No"},
        {"Name": "Md Nisar Ahmed", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Nikitha R", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Niveditha Ramachandra", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Rakshith", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Rangaswamy H", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Sagar H", "Target SP": 16, "Senior Dev": "Yes"},
        {"Name": "Saranya R", "Target SP": None, "Senior Dev": "No"},
        {"Name": "Shuba A", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Sudheendra K", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "Urla Dileep Kumar", "Target SP": 15, "Senior Dev": "No"},
        {"Name": "vignesh k", "Target SP": 20, "Senior Dev": "Yes"},
        {"Name": "Vignesh Sekaran", "Target SP": 16, "Senior Dev": "Yes"},
        {"Name": "yogita.kotwal", "Target SP": 20, "Senior Dev": "Yes"},
    ]

    def fetch_issues(jql, fields, label):
        url = f"{JIRA_URL}/rest/api/3/search"
        headers = {"Accept": "application/json"}
        params = {"jql": jql, "maxResults": 1000, "fields": ",".join(fields)}
        response = requests.get(url, headers=headers, params=params, auth=HTTPBasicAuth(EMAIL, API_TOKEN))
        if response.status_code == 200:
            return response.json()["issues"]
        else:
            st.error(f"❌ ERROR for {label}: {response.status_code} - {response.text}")
            return []

    # === Build & display JQLs ===
    sprint_jql = f"sprint in ({SPRINT_ID}) AND issuetype = Story"
    bugfix_jql = (
        f"project = QA AND status in (Closed, QA, 'PR Raised', 'IN LOCAL') "
        f"AND updated >= {bugfix_start} AND updated <= {bugfix_end} AND issuetype = Bug"
    )
    regression_jql = (
        f"project = QA AND status in (Closed, QA, 'PR Raised', 'IN LOCAL') "
        f"AND updated >= {regression_start} AND updated <= {regression_end} AND issuetype = Regression"
    )
    dev_jql = (
        f"project = 'Development Activities' AND updated >= {dev_start} AND updated <= {dev_end}"
    )
    ps_jql = (
        f"project = 'KPISOFT Prod Support' AND status in ('QA Passed', Closed) "
        f"AND updated >= {ps_start} AND updated <= {ps_end}"
    )

    # === Show JQLs in app ===
    st.subheader("🔍 JQLs Used")
    st.code(f"User Story JQL:\n{sprint_jql}")
    st.code(f"Bug Fix Effort (Bug) JQL:\n{bugfix_jql}")
    st.code(f"Regression JQL:\n{regression_jql}")
    st.code(f"DEV Ticket Effort JQL:\n{dev_jql}")
    st.code(f"PS Effort JQL:\n{ps_jql}")

    # === Run Queries ===
    sprint_issues = fetch_issues(sprint_jql, ["assignee", "timespent"], "User Stories")
    us_rows = []
    for issue in sprint_issues:
        assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None
        timespent = issue["fields"]["timespent"] or 0
        us_rows.append({"Name": assignee, "US_timespent": timespent})
    us_df = pd.DataFrame(us_rows)
    if not us_df.empty:
        us_df = us_df.groupby("Name").agg({"US_timespent": "sum", "Name": "count"}).rename(columns={"Name": "User Story Count"}).reset_index()
        us_df["User Story Effort"] = us_df["US_timespent"] / 60 / 60 / 8
        us_df = us_df.drop(columns=["US_timespent"])
    else:
        us_df = pd.DataFrame(columns=["Name", "User Story Effort", "User Story Count"])

    def extract_effort(issues, effort_col, count_col):
        rows = []
        for issue in issues:
            assignee = issue["fields"]["assignee"]["displayName"] if issue["fields"]["assignee"] else None
            timespent = issue["fields"]["timespent"] or 0
            rows.append({"Name": assignee, f"{effort_col}_sec": timespent})
        df = pd.DataFrame(rows)
        if df.empty:
            return pd.DataFrame(columns=["Name", effort_col, count_col])
        df_effort = df.groupby("Name").agg({f"{effort_col}_sec": "sum", "Name": "count"}).rename(columns={"Name": count_col}).reset_index()
        df_effort[effort_col] = df_effort[f"{effort_col}_sec"] / 60 / 60 / 8
        df_effort = df_effort.drop(columns=[f"{effort_col}_sec"])
        return df_effort

    bug_df = extract_effort(fetch_issues(bugfix_jql, ["assignee", "timespent"], "QA Fix Effort (Bug)"), "QA Fix Effort (Bug)", "Bug Count")

    reg_df = extract_effort(fetch_issues(regression_jql, ["assignee", "timespent"], "QA Fix Effort (Reg)"), "QA Fix Effort (Reg)", "Regression Count")

    dev_df = extract_effort(fetch_issues(dev_jql, ["assignee", "timespent"], "Dev ticket Effort"), "Dev ticket Effort", "DEV Count")

    ps_df = extract_effort(fetch_issues(ps_jql, ["assignee", "timespent"], "PS Effort"), "PS Effort", "PS Count")

    df = pd.DataFrame(resource_static)
    df = df.merge(us_df, on="Name", how="left")
    df = df.merge(bug_df, on="Name", how="left")
    df = df.merge(reg_df, on="Name", how="left")
    df = df.merge(dev_df, on="Name", how="left")
    df = df.merge(ps_df, on="Name", how="left")

    df = df.fillna(0).infer_objects(copy=False)

    df["Dev Effort (US+QAB+QAR+Dev)"] = df["User Story Effort"] + df["QA Fix Effort (Bug)"] + df["QA Fix Effort (Reg)"] + df["Dev ticket Effort"]
    df["Overall Effort"] = df["Dev Effort (US+QAB+QAR+Dev)"] + df["PS Effort"]
    df["Productivity (US+QAR+Dev+PS)"] = df["Overall Effort"]
    df["Delta"] = df["Productivity (US+QAR+Dev+PS)"]

    final_cols = [
        "Name", "Target SP", "Senior Dev",
        "User Story Effort", "QA Fix Effort (Bug)", "QA Fix Effort (Reg)", "Dev ticket Effort",
        "Dev Effort (US+QAB+QAR+Dev)", "PS Effort", "Overall Effort", "Productivity (US+QAR+Dev+PS)", "Delta",
        "User Story Count", "Bug Count", "Regression Count", "DEV Count", "PS Count"
    ]

    st.success("✅ Final Sprint Effort Breakdown")
    st.dataframe(df[final_cols])
    st.download_button("📥 Download Final Breakdown", df[final_cols].to_csv(index=False), "final_sprint_effort.csv")
