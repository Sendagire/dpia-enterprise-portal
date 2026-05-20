import streamlit as st
import google.generativeai as genai
import datetime
from docx import Document
from supabase import create_client

# --- 1. ENTERPRISE CONFIG ---
st.set_page_config(page_title="DPIA Enterprise", layout="wide")

# Configure Gemini
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
model = genai.GenerativeModel('gemini-3.1-flash-lite')

# Configure Supabase
supabase = create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])

# --- 2. AUTHENTICATION (The Bouncer) ---
if 'user' not in st.session_state:
    st.title("🛡️ DPIA Enterprise Login")
    with st.container(border=True):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Log In"):
            try:
                auth = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = auth.user
                st.rerun()
            except Exception as e:
                st.error("Login failed: " + str(e))
    st.stop() 

# --- 3. DASHBOARD (After Login) ---
st.title("🛡️ Assessment Dashboard")
st.write(f"Logged in as: {st.session_state.user.email}")
if st.button("Log Out"):
    st.session_state.clear()
    st.rerun()

# --- 4. PROJECT INPUTS ---
with st.container(border=True):
    st.subheader("📝 New DPIA Assessment")
    with st.form("dpia_form"):
        col1, col2 = st.columns(2, gap="medium")
        with col1:
            p_name = st.text_input("Project Name")
            data_subjects = st.text_input("Data Subjects")
        with col2:
            project_desc = st.text_area("Description")
            data_collected = st.text_area("Data Collected")
        
        submitted = st.form_submit_button("Analyze Privacy Risks", use_container_width=True)

if submitted:
    # A. AI Analysis (Using Gemini)
    with st.spinner("Analyzing risks with Gemini..."):
        prompt = f"Project: {p_name}\nDescription: {project_desc}\nData Collected: {data_collected}\n\nIdentify 3 privacy risks for this project. Provide Description and Mitigation for each."
        response = model.generate_content(prompt)
        risks = response.text
    
    st.write("### Identified Risks")
    st.markdown(risks)
    
    # B. Audit Trail (Save to Supabase)
    try:
        supabase.table("assessments").insert({
            "user_id": st.session_state.user.id,
            "project_name": p_name,
            "risks_output": risks,
            "created_at": str(datetime.datetime.now())
        }).execute()
    except Exception as e:
        st.warning("Audit trail could not be saved: " + str(e))
    
    # C. Generate Word Document
    doc = Document()
    doc.add_heading(f"DPIA Report: {p_name}", 0)
    doc.add_paragraph(f"Generated on: {datetime.datetime.now()}")
    doc.add_paragraph(risks)
    
    # Save to a temporary file in memory
    from io import BytesIO
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    
    st.download_button(
        label="Download Final Word Document",
        data=buffer,
        file_name="DPIA_Final.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
