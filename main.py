import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📈 JCFAP usage report")

# Upload section
uploaded_file = st.file_uploader("📤 Upload your login CSV file", type=["csv"])

if uploaded_file:
    try:
        # Read CSV
        df = pd.read_csv(uploaded_file)

        # Parse timestamp
        df["@timestamp"] = pd.to_datetime(
            df["@timestamp"].str.replace("@", "", regex=False).str.strip(),
            format="%b %d, %Y %H:%M:%S.%f"
        )

        # Add useful datetime columns
        df["date"] = df["@timestamp"].dt.date
        df["month"] = df["@timestamp"].dt.month_name()

        # Month filter dropdown
        months = df["month"].unique().tolist()
        selected_month = st.selectbox("📅 Select Month", options=["All"] + sorted(months, key=lambda m: datetime.strptime(m, "%B").month))

        if selected_month != "All":
            df_filtered = df[df["month"] == selected_month]
        else:
            df_filtered = df.copy()

        # ---------- Compute Summary ----------
        def compute_summary(df):
            daily_logins = df.groupby("date").size().reset_index(name="Login Count")
            daily_logins["Month"] = selected_month if selected_month != "All" else "Multiple"
            return daily_logins

        def compute_metrics(df):
            if df.empty:
                return {}

            registered_users = df["user_email"].nunique()

            # DAU: average daily unique logins
            dau_series = df.groupby("date")["user_email"].nunique()
            dau_avg = dau_series.mean()

            # MAU: monthly unique users
            mau = registered_users

            # Login behavior
            login_counts = df["user_email"].value_counts()
            repeat_login_pct = login_counts[login_counts > 1].count() / registered_users * 100 if registered_users else 0
            unique_login_pct = login_counts[login_counts == 1].count() / registered_users * 100 if registered_users else 0

            dau_mau_ratio = (dau_avg / mau) * 100 if mau > 0 else 0

            month_name = df["month"].mode()[0] if not df["month"].mode().empty else "N/A"

            return {
                "Month": month_name,
                "Registered": registered_users,
                "DAU(Avg)": round(dau_avg, 2),
                "MAU": mau,
                "Repeat Logins": f"{repeat_login_pct:.0f}%",
                "Unique Logins": f"{unique_login_pct:.0f}%",
                "DAU/MAU(%)": f"{dau_mau_ratio:.0f}%"
            }

        # ---------- Results ----------
        summary_df = compute_summary(df_filtered)
        metrics = compute_metrics(df_filtered)

        # ⏱️ Daily login summary with drill-down
        st.subheader("📅 Daily Login Summary")

        st.write("Select a date to see the list of users who logged in:")

        dates = summary_df["date"].astype(str).tolist()
        selected_date = st.selectbox("Select Date", options=["None"] + dates)

        st.dataframe(summary_df)

        if selected_date != "None":
            selected_date_obj = pd.to_datetime(selected_date).date()
            users_on_date = df_filtered[df_filtered["date"] == selected_date_obj][["user_email", "@timestamp"]].sort_values("@timestamp")
            st.subheader(f"👥 Users logged in on {selected_date}")
            st.dataframe(users_on_date.reset_index(drop=True))

        # 📊 Login Metrics
        st.subheader("📊 Login and Activation Metrics")
        if metrics:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🗓️ Month", metrics["Month"])
                st.metric("👤 Registered", metrics["Registered"])
            with col2:
                st.metric("📆 DAU (Avg)", metrics["DAU(Avg)"])
                st.metric("📅 MAU", metrics["MAU"])
            with col3:
                st.metric("🔁 Repeat Logins", metrics["Repeat Logins"])
                st.metric("✅ Unique Logins", metrics["Unique Logins"])
                st.metric("📊 DAU/MAU (%)", metrics["DAU/MAU(%)"])

            # Optional: Raw metrics for selected month
            with st.expander("🔍 Show Raw Metrics Table"):
                st.dataframe(pd.DataFrame([metrics]))

        # 📋 All Months Metrics Summary
        st.subheader("📋 Monthly Metrics Overview")

        # Compute metrics for each month and collect
        monthly_metrics = []
        for month in sorted(df["month"].unique(), key=lambda m: datetime.strptime(m, "%B").month):
            df_month = df[df["month"] == month]
            month_metrics = compute_metrics(df_month)
            monthly_metrics.append(month_metrics)

        metrics_df = pd.DataFrame(monthly_metrics)

        with st.expander("🔍 Show Raw Metrics Table for All Months"):
            st.dataframe(metrics_df)

            # CSV download
            csv = metrics_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Metrics as CSV",
                data=csv,
                file_name="monthly_login_metrics.csv",
                mime="text/csv"
            )

    except Exception as e:
        st.error(f"❌ Error while processing: {e}")

else:
    st.info("Please upload your login CSV file to begin.")
