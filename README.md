# Blood Donor Finder and Management System

Beginner-friendly B.Tech live project using Python, Streamlit, SQLite, Pandas and Plotly.

## Modules
- Home dashboard with statistics and charts
- Donor registration with consent
- Search donors by blood group, city and area
- Donor contact information
- Blood donation history
- Donor records and availability updates
- About project

## Run locally
Install Python 3.10+, open terminal in this folder and run:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy
Push these files to GitHub. At https://share.streamlit.io/ choose Create app, select your repository, branch `main`, main file `app.py`, then Deploy.

## Privacy and safety
Use fictional records for demonstrations. Do not publish real donor personal details. Store/display contact details only with informed consent. Availability is self-reported and is not verified. The app does not determine donor eligibility or medical compatibility. For urgent needs, contact an authorised blood bank or hospital.

SQLite on Streamlit Community Cloud is not durable production storage. For real-world use, add authentication, access controls, consent withdrawal and a managed persistent database.
