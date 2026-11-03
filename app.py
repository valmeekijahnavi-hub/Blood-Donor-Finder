import sqlite3
from pathlib import Path
from datetime import date, datetime
import re
import pandas as pd
import plotly.express as px
import streamlit as st

DB = Path(__file__).with_name("blood_donor_finder.db")
GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
st.set_page_config(page_title="Blood Donor Finder", page_icon="🩸", layout="wide")

def connect():
    c = sqlite3.connect(DB, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with connect() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS donors(
            donor_id INTEGER PRIMARY KEY AUTOINCREMENT, full_name TEXT NOT NULL,
            age INTEGER NOT NULL, blood_group TEXT NOT NULL, city TEXT NOT NULL,
            area TEXT, phone TEXT NOT NULL, email TEXT, available INTEGER DEFAULT 1,
            consent INTEGER NOT NULL, created_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS donation_history(
            history_id INTEGER PRIMARY KEY AUTOINCREMENT, donor_id INTEGER NOT NULL,
            donation_date TEXT NOT NULL, hospital_or_camp TEXT, notes TEXT,
            FOREIGN KEY(donor_id) REFERENCES donors(donor_id))""")

def get_donors():
    with connect() as c:
        return pd.read_sql_query("SELECT * FROM donors ORDER BY donor_id DESC", c)

def get_history():
    with connect() as c:
        return pd.read_sql_query("""SELECT h.history_id,d.donor_id,d.full_name,d.blood_group,
            h.donation_date,h.hospital_or_camp,h.notes FROM donation_history h
            JOIN donors d ON d.donor_id=h.donor_id ORDER BY h.donation_date DESC""", c)

def phone_ok(p):
    return 10 <= len(re.sub(r"\\D", "", p)) <= 15

def add_donor(v):
    with connect() as c:
        c.execute("""INSERT INTO donors(full_name,age,blood_group,city,area,phone,email,
            available,consent,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (v["name"].strip(),v["age"],v["group"],v["city"].strip(),v["area"].strip(),
             v["phone"].strip(),v["email"].strip(),int(v["available"]),1,
             datetime.now().isoformat(timespec="seconds")))

def add_history(donor_id, donated, place, notes):
    with connect() as c:
        c.execute("INSERT INTO donation_history(donor_id,donation_date,hospital_or_camp,notes) VALUES(?,?,?,?)",
                  (donor_id,str(donated),place.strip(),notes.strip()))

def update_availability(donor_id, status):
    with connect() as c:
        c.execute("UPDATE donors SET available=? WHERE donor_id=?", (int(status),int(donor_id)))

init_db()
with st.sidebar:
    st.title("🩸 Blood Donor Finder")
    st.caption("Donor registration and search")
    page = st.radio("NAVIGATION", [
        "Home Dashboard","Donor Registration","Find Donors",
        "Donation History","Donor Records","About Project"
    ])
    st.divider()
    st.caption("B.Tech Live Project | Python + Streamlit + SQLite")

st.title("🩸 Blood Donor Finder and Management System")
st.caption("Find registered donor records by blood group and location.")
st.warning("Educational prototype only. Use fictional data for demonstrations. Donor availability is self-reported, not verified. This app does not assess donor eligibility or medical compatibility. For emergencies, contact a hospital or authorised blood bank.")

donors = get_donors()
history = get_history()

if page == "Home Dashboard":
    st.subheader("Home Dashboard")
    a,b,c,d = st.columns(4)
    a.metric("Total Donors",len(donors))
    b.metric("Available (self-reported)",int(donors["available"].sum()) if len(donors) else 0)
    c.metric("Cities Covered",donors["city"].nunique() if len(donors) else 0)
    d.metric("Donation Records",len(history))
    left,right = st.columns(2)
    with left:
        st.markdown("#### Donors by blood group")
        if len(donors):
            counts=donors.groupby("blood_group").size().reset_index(name="Donors")
            st.plotly_chart(px.bar(counts,x="blood_group",y="Donors",color="blood_group"),use_container_width=True)
        else: st.info("Register sample donors to display statistics.")
    with right:
        st.markdown("#### Donors by city")
        if len(donors):
            counts=donors.groupby("city").size().reset_index(name="Donors")
            st.plotly_chart(px.pie(counts,names="city",values="Donors",hole=.35),use_container_width=True)
        else: st.info("City chart will appear after registration.")
    st.markdown("#### Recently registered donors")
    if len(donors):
        st.dataframe(donors[["donor_id","full_name","blood_group","city","available"]].head(8),use_container_width=True,hide_index=True)

elif page == "Donor Registration":
    st.subheader("➕ Donor Registration")
    st.write("Register a donor only with their informed permission.")
    with st.form("register",clear_on_submit=True):
        x,y=st.columns(2)
        with x:
            name=st.text_input("Full name *")
            age=st.number_input("Age *",18,100,18)
            group=st.selectbox("Blood group *",GROUPS)
            city=st.text_input("City / town *")
        with y:
            area=st.text_input("Area / locality")
            phone=st.text_input("Contact number *")
            email=st.text_input("Email (optional)")
            available=st.selectbox("Willing to be contacted?",["Yes","No"])=="Yes"
        consent=st.checkbox("I have permission to store and display this donor's contact details. *")
        submit=st.form_submit_button("Register Donor",type="primary",use_container_width=True)
        if submit:
            if not name.strip() or not city.strip() or not phone.strip(): st.error("Complete all required fields.")
            elif not phone_ok(phone): st.error("Enter a phone number containing 10–15 digits.")
            elif not consent: st.error("Donor consent is required.")
            else:
                add_donor({"name":name,"age":int(age),"group":group,"city":city,"area":area,
                           "phone":phone,"email":email,"available":available})
                st.success("Donor registered successfully.")

elif page == "Find Donors":
    st.subheader("🔎 Find Donors")
    x,y,z=st.columns(3)
    group=x.selectbox("Blood group",["All"]+GROUPS)
    city=y.text_input("City")
    area=z.text_input("Area / locality")
    result=donors.copy()
    if len(result):
        result=result[result.available==1]
        if group!="All": result=result[result.blood_group==group]
        if city.strip(): result=result[result.city.str.contains(city.strip(),case=False,na=False)]
        if area.strip(): result=result[result.area.fillna("").str.contains(area.strip(),case=False,na=False)]
    st.subheader(f"{len(result)} matching donor record(s)")
    if len(result):
        st.dataframe(result[["donor_id","full_name","age","blood_group","city","area","phone","email"]],
                     use_container_width=True,hide_index=True)
        st.caption("Contact information is shown only for consented demonstration records. Confirm details directly.")
    else: st.info("No matching available records. Try another blood group or location.")

elif page == "Donation History":
    st.subheader("🩸 Blood Donation History")
    if donors.empty: st.info("Register a donor before adding donation history.")
    else:
        choices={f'{r.full_name} — ID {r.donor_id} ({r.blood_group})':int(r.donor_id) for r in donors.itertuples()}
        with st.form("history",clear_on_submit=True):
            choice=st.selectbox("Donor",list(choices))
            donated=st.date_input("Donation date",value=date.today(),max_value=date.today())
            place=st.text_input("Hospital / donation camp")
            notes=st.text_area("Notes (optional)")
            if st.form_submit_button("Save Donation Record",type="primary"):
                add_history(choices[choice],donated,place,notes)
                st.success("Donation history saved.")
    st.markdown("#### Previous donation records")
    if history.empty: st.info("No donation history recorded.")
    else: st.dataframe(history,use_container_width=True,hide_index=True)

elif page == "Donor Records":
    st.subheader("🗂️ Donor Records Dashboard")
    if donors.empty: st.info("No donor records yet.")
    else:
        q=st.text_input("Search by donor name, city or ID")
        view=donors.copy()
        if q.strip():
            mask=(view.full_name.str.contains(q,case=False,na=False) |
                  view.city.str.contains(q,case=False,na=False) |
                  view.donor_id.astype(str).str.contains(q,case=False,na=False))
            view=view[mask]
        st.dataframe(view,use_container_width=True,hide_index=True)
        st.markdown("#### Update donor availability")
        chosen=st.selectbox("Donor ID",donors.donor_id.tolist())
        row=donors[donors.donor_id==chosen].iloc[0]
        status=st.selectbox("Availability",["Available","Not available"],index=0 if row.available else 1)
        if st.button("Update availability"):
            update_availability(chosen,status=="Available")
            st.success("Availability updated. Refresh the page to view the latest value.")

else:
    st.subheader("ℹ️ About Project")
    st.markdown("""
    **Project title:** Blood Donor Finder and Management System

    **Objective:** To develop a web application that helps people search for registered blood donors based on blood group and city.

    **Main modules**
    - Home dashboard
    - Donor registration
    - Blood group selection
    - Search donors by blood group
    - Location-based donor search
    - Donor contact information
    - Blood donation history
    - Donor records dashboard
    - About project

    **Technology stack:** Python, Streamlit, SQLite, Pandas and Plotly.

    **Future enhancements:** Secure login, verified blood-bank partnerships, consent withdrawal, secure cloud database, notification preferences and multilingual support.
    """)
    st.info("This student prototype is not an authorised blood bank or a medical advice service.")
