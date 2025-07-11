# import streamlit as st
# import pandas as pd
# import requests
# from requests.auth import HTTPBasicAuth
# from datetime import datetime
# from collections import defaultdict

# # === Streamlit page ===
# st.set_page_config(page_title="📊 Jira Effort Breakdown - Entomo", layout="wide")
# st.title("📊 Jira Effort Breakdown")

# # === Sidebar inputs ===
# st.sidebar.header("🔑 Jira API Config")
# JIRA_URL = st.sidebar.text_input("Jira URL", "https://kpisoft.atlassian.net/")
# EMAIL = st.sidebar.text_input("Email", "swaraj.s@entomo.co")
# API_TOKEN = st.sidebar.text_input("API Token", type="password")

# st.sidebar.header("📅 Default Date Range")
# default_start_date = st.sidebar.date_input("Default Start Date", datetime.strptime("2025-05-05", "%Y-%m-%d").date())
# default_end_date = st.sidebar.date_input("Default End Date", datetime.strptime("2025-06-01", "%Y-%m-%d").date())

# st.sidebar.header("🏃 Sprint")
# SPRINT_ID = st.sidebar.text_input("Sprint ID", "722")

# # === Fetch Sprint Name ===
# def fetch_sprint_name(sprint_id):
#     url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}"
#     headers = {"Accept": "application/json"}
#     try:
#         response = requests.get(url, headers=headers, auth=HTTPBasicAuth(EMAIL, API_TOKEN))
#         if response.status_code == 200:
#             data = response.json()
#             return data.get("name", f"ID: {sprint_id}")
#         else:
#             return f"ID: {sprint_id}"
#     except:
#         return f"ID: {sprint_id}"

# SPRINT_NAME = fetch_sprint_name(SPRINT_ID)
# st.subheader(f"🏷️ Sprint: {SPRINT_NAME}")

# st.sidebar.header("🔧 Phase Date Overrides")
# qa_start = st.sidebar.date_input("QA Start Date", default_start_date)
# qa_end = st.sidebar.date_input("QA End Date", default_end_date)

# dev_start = st.sidebar.date_input("DEV Start Date", default_start_date)
# dev_end = st.sidebar.date_input("DEV End Date", default_end_date)

# ps_start = st.sidebar.date_input("PS Start Date", default_start_date)
# ps_end = st.sidebar.date_input("PS End Date", default_end_date)

# if st.sidebar.button("🚀 Run Effort Breakdown"):

#     def fetch_issues(jql, with_changelog=False):
#         url = f"{JIRA_URL}/rest/api/3/search"
#         headers = {"Accept": "application/json"}
#         start_at = 0
#         max_results = 50 if with_changelog else 100
#         all_issues = []

#         while True:
#             params = {
#                 "jql": jql,
#                 "startAt": start_at,
#                 "maxResults": max_results,
#                 "fields": "assignee,issuetype,timespent",
#                 "expand": "changelog" if with_changelog else ""
#             }
#             response = requests.get(url, headers=headers, params=params, auth=HTTPBasicAuth(EMAIL, API_TOKEN))
#             if response.status_code != 200:
#                 st.error(f"❌ API Error: {response.status_code} - {response.text}")
#                 return []

#             data = response.json()
#             issues = data.get("issues", [])
#             all_issues.extend(issues)

#             if len(issues) < max_results:
#                 break

#             start_at += max_results

#         return all_issues

#     # === JQLs ===
#     QA_JQL = f"""
#         project = QA AND status in (Closed, QA, "PR Raised", "IN LOCAL")
#         AND updated >= {qa_start} AND updated <= {qa_end}
#     """.replace("\n", " ").strip()

#     US_JQL = f"sprint in ({SPRINT_ID}) AND issuetype = Story"
#     DEV_JQL = f"project = \"Development Activities\" AND updated >= {dev_start} AND updated <= {dev_end}"
#     PS_JQL = f"project = \"KPISOFT Prod Support\" AND status in (\"QA Passed\", Closed) AND updated >= {ps_start} AND updated <= {ps_end}"

#     # === Fetch ===
#     qa_issues = fetch_issues(QA_JQL)
#     us_issues = fetch_issues(US_JQL, with_changelog=True)
#     dev_issues = fetch_issues(DEV_JQL)
#     ps_issues = fetch_issues(PS_JQL)

#     def build_effort_df(issues, effort_col_name):
#         rows = []
#         for issue in issues:
#             f = issue["fields"]
#             assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
#             timespent = f.get("timespent") or 0
#             rows.append({
#                 "Assignee": assignee.strip(),
#                 "Timespent_days": timespent / 60 / 60 / 8
#             })
#         df = pd.DataFrame(rows)
#         if not df.empty:
#             return df.groupby("Assignee").agg({"Timespent_days": "sum"}).reset_index().rename(columns={"Timespent_days": effort_col_name})
#         else:
#             return pd.DataFrame(columns=["Assignee", effort_col_name])

#     bug_issues = [i for i in qa_issues if i["fields"]["issuetype"]["name"].lower() == "bug"]
#     reg_issues = [i for i in qa_issues if i["fields"]["issuetype"]["name"].lower() == "regression"]

#     bug_df = build_effort_df(bug_issues, "QA Fix Effort? (Bug)")
#     reg_df = build_effort_df(reg_issues, "QA Fix Effort? (Reg)")
#     us_df = build_effort_df(us_issues, "User Story Effort")
#     dev_df = build_effort_df(dev_issues, "Dev ticket Effort")
#     ps_df = build_effort_df(ps_issues, "PS Effort")

#     # === Transition Count ===
#     transition_counts = defaultdict(int)
#     for issue in us_issues:
#         f = issue["fields"]
#         assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
#         changelog = issue.get("changelog", {})
#         histories = changelog.get("histories", [])
#         count = sum(1 for entry in histories for item in entry.get("items", []) if item.get("field") == "status")
#         transition_counts[assignee.strip()] += count

#     trans_df = pd.DataFrame(list(transition_counts.items()), columns=["Name?", "Transition Count"])

#     # === Merge Jira data ===
#     final_df = bug_df.merge(reg_df, on="Assignee", how="outer") \
#                      .merge(us_df, on="Assignee", how="outer") \
#                      .merge(dev_df, on="Assignee", how="outer") \
#                      .merge(ps_df, on="Assignee", how="outer") \
#                      .fillna(0)

#     final_df["Dev Effort (US+QAB+QAR+Dev)"] = final_df["User Story Effort"] + final_df["QA Fix Effort? (Bug)"] + final_df["QA Fix Effort? (Reg)"] + final_df["Dev ticket Effort"]
#     final_df["Overall Effort"] = final_df["Dev Effort (US+QAB+QAR+Dev)"] + final_df["PS Effort"]
#     final_df.rename(columns={"Assignee": "Name?"}, inplace=True)

#     st.write("✅ Raw Effort:", final_df)

#     # === Unique counts ===
#     def count_unique(issues):
#         counts = defaultdict(set)
#         for issue in issues:
#             f = issue["fields"]
#             assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
#             key = issue["id"]
#             counts[assignee.strip()].add(key)
#         return {k: len(v) for k, v in counts.items()}

#     dev_count = count_unique(dev_issues)
#     us_count = count_unique(us_issues)
#     ps_count = count_unique(ps_issues)
#     qar_count = count_unique(reg_issues)

#     dev_count_df = pd.DataFrame(list(dev_count.items()), columns=["Name?", "Dev Count"])
#     us_count_df = pd.DataFrame(list(us_count.items()), columns=["Name?", "US Count"])
#     ps_count_df = pd.DataFrame(list(ps_count.items()), columns=["Name?", "PS Count"])
#     qar_count_df = pd.DataFrame(list(qar_count.items()), columns=["Name?", "QAR Count"])

#     # === Final merge ===
#     people = [
#         {"Name?": "Abhishek Patro", "Target SP": None, "Senior Dev": "No"},
#         {"Name?": "Amit Krishna", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Avinash S", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Chaithra B", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "chandan k", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Dhaarani Devi", "Target SP": None, "Senior Dev": "No"},
#         {"Name?": "Gangadhara S M", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Harish Ramakrishna", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Krishna S", "Target SP": None, "Senior Dev": "No"},
#         {"Name?": "Md Nisar Ahmed", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Nikitha R", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Niveditha Ramachandra", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Rakshith", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Rangaswamy H", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Sagar H", "Target SP": 16, "Senior Dev": "Yes"},
#         {"Name?": "Saranya R", "Target SP": None, "Senior Dev": "No"},
#         {"Name?": "Shuba A", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Sudheendra K", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "Urla Dileep Kumar", "Target SP": 15, "Senior Dev": "No"},
#         {"Name?": "vignesh k", "Target SP": 20, "Senior Dev": "Yes"},
#         {"Name?": "Vignesh Sekaran", "Target SP": 16, "Senior Dev": "Yes"},
#         {"Name?": "yogita.kotwal", "Target SP": 20, "Senior Dev": "Yes"}
#     ]
#     people_df = pd.DataFrame(people)
#     merged = people_df.merge(final_df, on="Name?", how="left").fillna(0)
#     merged = merged.merge(dev_count_df, on="Name?", how="left").fillna(0)
#     merged = merged.merge(us_count_df, on="Name?", how="left").fillna(0)
#     merged = merged.merge(ps_count_df, on="Name?", how="left").fillna(0)
#     merged = merged.merge(qar_count_df, on="Name?", how="left").fillna(0)
#     merged = merged.merge(trans_df, on="Name?", how="left").fillna(0)

#     # === Correct Productivity and Delta ===
#     merged["Productivity (US+QAR+Dev+PS)?"] = merged["User Story Effort"] + merged["QA Fix Effort? (Reg)"] + merged["Dev ticket Effort"] + merged["PS Effort"]
#     merged["Delta"] = merged.apply(
#         lambda row: row["Productivity (US+QAR+Dev+PS)?"] - row["Target SP"]
#         if row["Target SP"] not in [0, None] else row["Productivity (US+QAR+Dev+PS)?"],
#         axis=1
#     )

#     ordered_cols = [
#         "Name?", "Target SP", "Senior Dev", "User Story Effort", "QA Fix Effort? (Bug)", "QA Fix Effort? (Reg)",
#         "Dev ticket Effort", "Dev Effort (US+QAB+QAR+Dev)", "PS Effort", "Overall Effort",
#         "Productivity (US+QAR+Dev+PS)?", "Delta", "Dev Count", "US Count", "PS Count", "QAR Count", "Transition Count"
#     ]

#     merged = merged[ordered_cols]

#     # === Add total row ===
#     total_row = pd.DataFrame(merged.iloc[:, 3:].sum()).transpose()
#     total_row.insert(0, "Name?", "TOTAL")
#     total_row.insert(1, "Target SP", "")
#     total_row.insert(2, "Senior Dev", "")

#     final_df_with_total = pd.concat([merged, total_row], ignore_index=True)
#     st.write("✅ Final Merged:", final_df_with_total)
import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
from collections import defaultdict

# === Streamlit page ===
st.set_page_config(page_title="📊 Jira Effort Breakdown - Entomo", layout="wide")
st.title("📊 Jira Effort Breakdown")

# === Sidebar inputs ===
st.sidebar.header("🔑 Jira API Config")
JIRA_URL = st.sidebar.text_input("Jira URL", "https://kpisoft.atlassian.net/")
EMAIL = st.sidebar.text_input("Email", "swaraj.s@entomo.co")
API_TOKEN = st.sidebar.text_input("API Token", type="password")

st.sidebar.header("📅 Default Date Range")
default_start_date = st.sidebar.date_input("Default Start Date", datetime.strptime("2025-05-05", "%Y-%m-%d").date())
default_end_date = st.sidebar.date_input("Default End Date", datetime.strptime("2025-06-01", "%Y-%m-%d").date())

st.sidebar.header("🏃 Sprint")
SPRINT_ID = st.sidebar.text_input("Sprint ID", "722")

# === Fetch Sprint Name ===
def fetch_sprint_name(sprint_id):
    url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}"
    headers = {"Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, auth=HTTPBasicAuth(EMAIL, API_TOKEN))
        if response.status_code == 200:
            data = response.json()
            return data.get("name", f"ID: {sprint_id}")
        else:
            return f"ID: {sprint_id}"
    except:
        return f"ID: {sprint_id}"

SPRINT_NAME = fetch_sprint_name(SPRINT_ID)
st.subheader(f"🏷️ Sprint: {SPRINT_NAME}")

st.sidebar.header("🔧 Phase Date Overrides")
qa_start = st.sidebar.date_input("QA Start Date", default_start_date)
qa_end = st.sidebar.date_input("QA End Date", default_end_date)

dev_start = st.sidebar.date_input("DEV Start Date", default_start_date)
dev_end = st.sidebar.date_input("DEV End Date", default_end_date)

ps_start = st.sidebar.date_input("PS Start Date", default_start_date)
ps_end = st.sidebar.date_input("PS End Date", default_end_date)

if st.sidebar.button("🚀 Run Effort Breakdown"):

    def fetch_issues(jql, with_changelog=False):
        url = f"{JIRA_URL}/rest/api/3/search"
        headers = {"Accept": "application/json"}
        start_at = 0
        max_results = 50 if with_changelog else 100
        all_issues = []

        while True:
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "assignee,issuetype,timespent",
                "expand": "changelog" if with_changelog else ""
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

    # === JQLs ===
    QA_JQL = f"""
        project = QA AND status in (Closed, QA, "PR Raised", "IN LOCAL")
        AND updated >= {qa_start} AND updated <= {qa_end}
    """.replace("\n", " ").strip()

    US_JQL = f"sprint in ({SPRINT_ID}) AND issuetype = Story"
    DEV_JQL = f"project = \"Development Activities\" AND updated >= {dev_start} AND updated <= {dev_end}"
    PS_JQL = f"project = \"KPISOFT Prod Support\" AND status in (\"QA Passed\", Closed) AND updated >= {ps_start} AND updated <= {ps_end}"

    # === Fetch ===
    qa_issues = fetch_issues(QA_JQL)
    us_issues = fetch_issues(US_JQL, with_changelog=True)
    dev_issues = fetch_issues(DEV_JQL)
    ps_issues = fetch_issues(PS_JQL)

    def build_effort_df(issues, effort_col_name):
        rows = []
        for issue in issues:
            f = issue["fields"]
            assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
            timespent = f.get("timespent") or 0
            rows.append({
                "Assignee": assignee.strip(),
                "Timespent_days": timespent / 60 / 60 / 8
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            return df.groupby("Assignee").agg({"Timespent_days": "sum"}).reset_index().rename(columns={"Timespent_days": effort_col_name})
        else:
            return pd.DataFrame(columns=["Assignee", effort_col_name])

    bug_issues = [i for i in qa_issues if i["fields"]["issuetype"]["name"].lower() == "bug"]
    reg_issues = [i for i in qa_issues if i["fields"]["issuetype"]["name"].lower() == "regression"]

    bug_df = build_effort_df(bug_issues, "QA Fix Effort? (Bug)")
    reg_df = build_effort_df(reg_issues, "QA Fix Effort? (Reg)")
    us_df = build_effort_df(us_issues, "User Story Effort")
    dev_df = build_effort_df(dev_issues, "Dev ticket Effort")
    ps_df = build_effort_df(ps_issues, "PS Effort")

    # === Transition Count ===
    transition_counts = defaultdict(set)
    for issue in us_issues:
        f = issue["fields"]
        assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
        changelog = issue.get("changelog", {})
        histories = changelog.get("histories", [])
        has_transition = any(item.get("field") == "status" for entry in histories for item in entry.get("items", []))
        if has_transition:
            transition_counts[assignee.strip()].add(issue["id"])

    # Final unique count per assignee
    trans_df = pd.DataFrame(
        [(assignee, len(ids)) for assignee, ids in transition_counts.items()],
        columns=["Name?", "Transition Count"]
    )

    # === Merge Jira data ===
    final_df = bug_df.merge(reg_df, on="Assignee", how="outer") \
                     .merge(us_df, on="Assignee", how="outer") \
                     .merge(dev_df, on="Assignee", how="outer") \
                     .merge(ps_df, on="Assignee", how="outer") \
                     .fillna(0)

    final_df["Dev Effort (US+QAB+QAR+Dev)"] = final_df["User Story Effort"] + final_df["QA Fix Effort? (Bug)"] + final_df["QA Fix Effort? (Reg)"] + final_df["Dev ticket Effort"]
    final_df["Overall Effort"] = final_df["Dev Effort (US+QAB+QAR+Dev)"] + final_df["PS Effort"]
    final_df.rename(columns={"Assignee": "Name?"}, inplace=True)

    st.write("✅ Raw Effort:", final_df)

    # === Unique counts ===
    def count_unique(issues):
        counts = defaultdict(set)
        for issue in issues:
            f = issue["fields"]
            assignee = f["assignee"]["displayName"] if f["assignee"] else "Unassigned"
            key = issue["id"]
            counts[assignee.strip()].add(key)
        return {k: len(v) for k, v in counts.items()}

    dev_count = count_unique(dev_issues)
    us_count = count_unique(us_issues)
    ps_count = count_unique(ps_issues)
    qar_count = count_unique(reg_issues)

    dev_count_df = pd.DataFrame(list(dev_count.items()), columns=["Name?", "Dev Count"])
    us_count_df = pd.DataFrame(list(us_count.items()), columns=["Name?", "US Count"])
    ps_count_df = pd.DataFrame(list(ps_count.items()), columns=["Name?", "PS Count"])
    qar_count_df = pd.DataFrame(list(qar_count.items()), columns=["Name?", "QAR Count"])

    # === Final merge ===
    people = [
     {"Name?": "Abhishek Patro", "Target SP": None, "Senior Dev": "No"},
    {"Name?": "Amit Krishna", "Target SP": 21, "Senior Dev": "Yes"},
    {"Name?": "Avinash S", "Target SP": 21, "Senior Dev": "Yes"},
    {"Name?": "Chaithra B", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "chandan k", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Dhaarani Devi", "Target SP": None, "Senior Dev": "No"},
    {"Name?": "Gangadhara S M", "Target SP": 21, "Senior Dev": "Yes"},
    {"Name?": "Harish Ramakrishna", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Krishna S", "Target SP": None, "Senior Dev": "No"},
    {"Name?": "Md Nisar Ahmed", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Nikitha R", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Niveditha Ramachandra", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Rakshith", "Target SP": 21, "Senior Dev": "Yes"},
    {"Name?": "Rangaswamy H", "Target SP": 20, "Senior Dev": "Yes"},
    {"Name?": "Sagar H", "Target SP": 18, "Senior Dev": "Yes"},
    {"Name?": "Saranya R", "Target SP": None, "Senior Dev": "No"},
    {"Name?": "Shuba A", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Sudheendra K", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "Urla Dileep Kumar", "Target SP": 16, "Senior Dev": "No"},
    {"Name?": "vignesh k", "Target SP": 21, "Senior Dev": "Yes"},
    {"Name?": "Vignesh Sekaran", "Target SP": 18, "Senior Dev": "Yes"},
    {"Name?": "yogita.kotwal", "Target SP": 21, "Senior Dev": "Yes"}
    
    ]
    
    people_df = pd.DataFrame(people)
    merged = people_df.merge(final_df, on="Name?", how="left").fillna(0)
    merged = merged.merge(dev_count_df, on="Name?", how="left").fillna(0)
    merged = merged.merge(us_count_df, on="Name?", how="left").fillna(0)
    merged = merged.merge(ps_count_df, on="Name?", how="left").fillna(0)
    merged = merged.merge(qar_count_df, on="Name?", how="left").fillna(0)
    merged = merged.merge(trans_df, on="Name?", how="left").fillna(0)

    # === Correct Productivity and Delta ===
    merged["Productivity (US+QAR+Dev+PS)?"] = merged["User Story Effort"] + merged["QA Fix Effort? (Reg)"] + merged["Dev ticket Effort"] + merged["PS Effort"]
    merged["Delta"] = merged.apply(
        lambda row: row["Productivity (US+QAR+Dev+PS)?"] - row["Target SP"]
        if row["Target SP"] not in [0, None] else row["Productivity (US+QAR+Dev+PS)?"],
        axis=1
    )

    ordered_cols = [
        "Name?", "Target SP", "Senior Dev", "User Story Effort", "QA Fix Effort? (Bug)", "QA Fix Effort? (Reg)",
        "Dev ticket Effort", "Dev Effort (US+QAB+QAR+Dev)", "PS Effort", "Overall Effort",
        "Productivity (US+QAR+Dev+PS)?", "Delta", "Dev Count", "US Count", "PS Count", "QAR Count", "Transition Count"
    ]

    merged = merged[ordered_cols]

    # === Add total row ===
    total_row = pd.DataFrame(merged.iloc[:, 3:].sum()).transpose()
    total_row.insert(0, "Name?", "TOTAL")
    total_row.insert(1, "Target SP", "")
    total_row.insert(2, "Senior Dev", "")

    final_df_with_total = pd.concat([merged, total_row], ignore_index=True)
    st.write("✅ Final Merged:", final_df_with_total)


