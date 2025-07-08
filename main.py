import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# === Streamlit page ===
st.set_page_config(page_title="📊 Jira Effort Breakdown", layout="wide")
st.title("📊 Jira Effort Breakdown (Multiple JQL, Real-time)")

# === Inputs ===
st.sidebar.header("🔑 Jira API Config")
JIRA_URL = st.sidebar.text_input("Jira URL", "https://kpisoft.atlassian.net/")
EMAIL = st.sidebar.text_input("Email", "swaraj.s@entomo.co")
API_TOKEN = st.sidebar.text_input("API Token", type="password")

default_start_date = datetime.strptime("2025-05-05", "%Y-%m-%d").date()
default_end_date = datetime.strptime("2025-06-01", "%Y-%m-%d").date()

# === Improved UI ===
st.sidebar.header("📅 Sprint & Date Ranges")
SPRINT_ID = st.sidebar.text_input("Sprint ID", "722")

qa_start = st.sidebar.date_input("QA Start Date", default_start_date)
qa_end = st.sidebar.date_input("QA End Date", default_end_date)

dev_start = st.sidebar.date_input("DEV Start Date", default_start_date)
dev_end = st.sidebar.date_input("DEV End Date", default_end_date)

ps_start = st.sidebar.date_input("PS Start Date", default_start_date)
ps_end = st.sidebar.date_input("PS End Date", default_end_date)

if st.sidebar.button("🚀 Run Effort Breakdown"):

    # === JQLs ===
    QA_JQL = f"""
        project = QA AND status in (Closed, QA, "PR Raised", "IN LOCAL")
        AND updated >= {qa_start} AND updated <= {qa_end}
        ORDER BY assignee
    """.replace("\n", " ").strip()

    US_JQL = f"""
        sprint in ({SPRINT_ID}) AND issuetype = Story
    """.replace("\n", " ").strip()

    DEV_JQL = f"""
        project = "Development Activities" AND updated >= {dev_start} AND updated <= {dev_end}
        ORDER BY assignee
    """.replace("\n", " ").strip()

    PS_JQL = f"""
        project = "KPISOFT Prod Support" AND status in ("QA Passed", Closed)
        AND updated >= {ps_start} AND updated <= {ps_end}
        ORDER BY assignee
    """.replace("\n", " ").strip()

    st.write("📌 QA JQL:", QA_JQL)
    st.write("📌 US JQL:", US_JQL)
    st.write("📌 DEV JQL:", DEV_JQL)
    st.write("📌 PS JQL:", PS_JQL)

    def fetch_issues(jql):
        url = f"{JIRA_URL}/rest/api/3/search"
        headers = {"Accept": "application/json"}
        start_at = 0
        max_results = 100
        all_issues = []

        while True:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "assignee,issuetype,timespent"
            }
            response = requests.get(url, headers=headers, params=params, auth=HTTPBasicAuth(EMAIL, API_TOKEN))
            if response.status_code != 200:
                st.error(f"❌ API Error: {response.status_code} - {response.text}")
                return []

            data = response.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            if len(issues) < max_results:
                break

            start_at += max_results

        return all_issues

    # === Fetch ===
    qa_issues = fetch_issues(QA_JQL)
    us_issues = fetch_issues(US_JQL)
    dev_issues = fetch_issues(DEV_JQL)
    ps_issues = fetch_issues(PS_JQL)

    st.write(f"✅ QA Issues: {len(qa_issues)}")
    st.write(f"✅ US Issues: {len(us_issues)}")
    st.write(f"✅ DEV Issues: {len(dev_issues)}")
    st.write(f"✅ PS Issues: {len(ps_issues)}")

    # === QA Effort: Bug & Reg ===
    qa_rows = []
    for issue in qa_issues:
        f = issue["fields"]
        assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
        issuetype = f["issuetype"]["name"]
        timespent = f.get("timespent") or 0
        qa_rows.append({
            "Assignee": assignee.strip(),
            "IssueType": issuetype,
            "Timespent_sec": timespent
        })
    qa_df = pd.DataFrame(qa_rows)
    if not qa_df.empty:
        qa_df["Timespent_days"] = qa_df["Timespent_sec"] / 60 / 60 / 8
    else:
        qa_df = pd.DataFrame(columns=["Assignee", "IssueType", "Timespent_sec", "Timespent_days"])

    bug_df = qa_df[qa_df["IssueType"].str.lower() == "bug"].groupby("Assignee").agg(
        Bug_Count=("IssueType", "count"),
        Bug_Effort=("Timespent_days", "sum")
    ).reset_index()

    reg_df = qa_df[qa_df["IssueType"].str.lower() == "regression"].groupby("Assignee").agg(
        Reg_Count=("IssueType", "count"),
        Reg_Effort=("Timespent_days", "sum")
    ).reset_index()

    # === User Story Effort ===
    us_rows = []
    for issue in us_issues:
        f = issue["fields"]
        assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
        timespent = f.get("timespent") or 0
        us_rows.append({
            "Assignee": assignee.strip(),
            "Timespent_sec": timespent
        })
    us_df = pd.DataFrame(us_rows)
    if not us_df.empty:
        us_df["Timespent_days"] = us_df["Timespent_sec"] / 60 / 60 / 8
        us_df = us_df.groupby("Assignee").agg(
            US_Count=("Timespent_sec", "count"),
            US_Effort=("Timespent_days", "sum")
        ).reset_index()
    else:
        us_df = pd.DataFrame(columns=["Assignee", "US_Count", "US_Effort"])

    # === DEV Effort ===
    dev_rows = []
    for issue in dev_issues:
        f = issue["fields"]
        assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
        timespent = f.get("timespent") or 0
        dev_rows.append({
            "Assignee": assignee.strip(),
            "Timespent_sec": timespent
        })
    dev_df = pd.DataFrame(dev_rows)
    if not dev_df.empty:
        dev_df["Timespent_days"] = dev_df["Timespent_sec"] / 60 / 60 / 8
        dev_df = dev_df.groupby("Assignee").agg(
            DEV_Count=("Timespent_sec", "count"),
            DEV_Effort=("Timespent_days", "sum")
        ).reset_index()
    else:
        dev_df = pd.DataFrame(columns=["Assignee", "DEV_Count", "DEV_Effort"])

    # === PS Effort ===
    ps_rows = []
    for issue in ps_issues:
        f = issue["fields"]
        assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
        timespent = f.get("timespent") or 0
        ps_rows.append({
            "Assignee": assignee.strip(),
            "Timespent_sec": timespent
        })
    ps_df = pd.DataFrame(ps_rows)
    if not ps_df.empty:
        ps_df["Timespent_days"] = ps_df["Timespent_sec"] / 60 / 60 / 8
        ps_df = ps_df.groupby("Assignee").agg(
            PS_Count=("Timespent_sec", "count"),
            PS_Effort=("Timespent_days", "sum")
        ).reset_index()
    else:
        ps_df = pd.DataFrame(columns=["Assignee", "PS_Count", "PS_Effort"])

    # === Final Merge & Format ===
    final_df = bug_df.merge(reg_df, on="Assignee", how="outer") \
                     .merge(us_df, on="Assignee", how="outer") \
                     .merge(dev_df, on="Assignee", how="outer") \
                     .merge(ps_df, on="Assignee", how="outer") \
                     .fillna(0)

    final_df["Dev Effort (US+QAB+QAR+Dev)"] = (
        final_df["Bug_Effort"] + final_df["Reg_Effort"] + final_df["US_Effort"] + final_df["DEV_Effort"]
    )

    final_df["Overall Effort"] = final_df["Dev Effort (US+QAB+QAR+Dev)"] + final_df["PS_Effort"]

    final_df["Productivity (US+QAR+Dev+PS)?"] = (
        final_df["US_Effort"] + final_df["Reg_Effort"] + final_df["DEV_Effort"] + final_df["PS_Effort"]
    )

    final_df.rename(columns={
        "Assignee": "Name?",
        "US_Effort": "User Story Effort",
        "Bug_Effort": "QA Fix Effort? (Bug)",
        "Reg_Effort": "QA Fix Effort? (Reg)",
        "DEV_Effort": "Dev ticket Effort",
        "PS_Effort": "PS Effort",
        "DEV_Count": "Dev Count",
        "US_Count": "US Count",
        "PS_Count": "PS Count"
    }, inplace=True)

    final_df = final_df[
        [
            "Name?",
            "User Story Effort",
            "QA Fix Effort? (Bug)",
            "QA Fix Effort? (Reg)",
            "Dev ticket Effort",
            "Dev Effort (US+QAB+QAR+Dev)",
            "PS Effort",
            "Overall Effort",
            "Productivity (US+QAR+Dev+PS)?",
            "Dev Count",
            "US Count",
            "PS Count"
        ]
    ]

    st.write("✅ Final Effort Breakdown (Formatted):")
    st.dataframe(final_df)

    csv = final_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Download CSV",
        data=csv,
        file_name="jira_effort_breakdown.csv",
        mime="text/csv"
    )
