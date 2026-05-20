import streamlit as st
import anthropic
import datetime
from docx import Document
from supabase import create_client

# --- 1. ENTERPRISE CONFIG ---
st.set_page_config(page_title="DPIA Enterprise", layout="centered")
client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

# --- 2. AUTHENTICATION (The Bouncer) ---
if 'user' not in st.session_state:
    st.title("🛡️ DPIA Enterprise Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Log In"):
        try:
            auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
            st.session_state.user = auth.user
            st.rerun()
        except Exception as e:
            st.error("Login failed: " + str(e))
    st.stop() # Stop here until logged in

# --- 3. DASHBOARD (After Login) ---
st.title("🛡️ Assessment Dashboard")
st.write(f"Logged in as: {st.session_state.user.email}")
if st.button("Log Out"):
    st.session_state.clear()
    st.rerun()

# --- 4. PROJECT INPUTS ---
with st.form("dpia_form"):
    col1, col2 = st.columns(2)
    with col1:
        p_name = st.text_input("Project Name")
        data_subjects = st.text_input("Data Subjects")
    with col2:
        project_desc = st.text_area("Description")
        data_collected = st.text_area("Data Collected")
    
    submitted = st.form_submit_button("Analyze Privacy Risks")

if submitted:
    # A. AI Analysis
    prompt = f"Identify 3 privacy risks for: {p_name}. Provide Description and Mitigation."
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    risks = response.content[0].text
    st.write("### Identified Risks")
    st.write(risks)
    
    # B. Audit Trail (Save to Supabase)
    supabase.table("assessments").insert({
        "user_id": st.session_state.user.id,
        "project_name": p_name,
        "risks_output": risks,
        "created_at": str(datetime.datetime.now())
    }).execute()
    
    # C. Generate Word Document
    doc = Document()
    doc.add_heading(f"DPIA Report: {p_name}", 0)
    doc.add_paragraph(f"Generated on: {datetime.datetime.now()}")
    doc.add_paragraph(risks)
    doc.save("DPIA_Final.docx")
    
    with open("DPIA_Final.docx", "rb") as f:
        st.download_button("Download Final Word Document", f, file_name="DPIA_Final.docx")