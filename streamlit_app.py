import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import datetime

# ---- Google Sheets Setup ----
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

# Use credentials from Streamlit secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
client = gspread.authorize(creds)

# Connect to spreadsheet and sheets
spreadsheet = client.open("Expense Manager")
expense_sheet = spreadsheet.worksheet("August 2025")
settings_sheet = spreadsheet.worksheet("Settings")  # Add new sheet named 'Settings'

# ---- Utility Functions ----
def get_total_monthly_amount():
    data = settings_sheet.get_all_records()
    for row in data:
        if row["Key"] == "total_monthly_amt":
            return float(row["Value"])
    return 0.0

def update_total_monthly_amount(new_amount):
    data = settings_sheet.get_all_records()
    for i, row in enumerate(data):
        if row["Key"] == "total_monthly_amt":
            settings_sheet.update_cell(i + 2, 2, new_amount)
            return

def calculate_remaining_balance():
    expenses = expense_sheet.get_all_records()
    total_spent = sum(float(row["Amount"]) for row in expenses)
    return get_total_monthly_amount() - total_spent

# ---- Streamlit UI ----
st.set_page_config(page_title="Expense Tracker", layout="centered")
st.title("💸 Expense Manager")

# Display Monthly Total & Balance
col1, col2 = st.columns(2)
with col1:
    total_amt = get_total_monthly_amount()
    new_total = st.number_input("Set Total Monthly Amount", min_value=0.0, value=total_amt, format="%.0f", key="monthly_amt")
    if st.button("Update Monthly Amount"):
        if new_total != total_amt:
            update_total_monthly_amount(new_total)
            st.success("Monthly total updated!")
            st.rerun()

with col2:
    remaining = calculate_remaining_balance()
    balance_color = "red" if remaining < 0 else "green"
    st.markdown(
        f"""
        <div style='background-color: white; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center;'>
            <h3 style='color: {balance_color}; margin: 0;'>Remaining Balance</h3>
            <h2 style='color: {balance_color}; margin: 0; font-weight:bold;'>₹ {remaining:.0f}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

# ---- Expense Form ----
st.subheader("Add your expense here")
with st.form("expense_form", clear_on_submit=True):
    date = st.date_input("Date", value=datetime.date.today())
    category = st.text_input("Enter Description for amount*")
    amount = st.number_input("Amount*", min_value=0.0, format="%.0f")
    note = st.text_input("Note (optional)")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        expense_sheet.append_row([str(date), category, amount, note])
        st.success("Expense added successfully!")
        st.rerun()

# ---- Display All Expenses ----
st.subheader("📊 Expense History")
data = expense_sheet.get_all_values()
headers = ["Date", "Desc", "Amount", "Note"]
rows = data[1:]

if rows:
    st.dataframe(rows, use_container_width=True)
else:
    st.info("No expenses recorded yet.")
