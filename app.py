import streamlit as st
import streamlit.components.v1 as components
import os

# Set page configuration to wide to allow the HTML to take up space
st.set_page_config(layout="wide", page_title="DPIA Enterprise")

# Read your custom HTML file
def load_html():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

# Render the HTML
# height=1200 ensures your entire landing page is visible without scrollbars
components.html(load_html(), height=1200, scrolling=True)
