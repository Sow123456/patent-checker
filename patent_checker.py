import base64
import json
import streamlit as st
import google.generativeai as genai
from fpdf import FPDF

st.set_page_config(page_title="Advanced Patent Suite", page_icon="🛡️", layout="wide")

# Encoded fallback Gemini API key (base64 obfuscation, not strong encryption)
ENCODED_GEMINI_KEY = "QUl6YVN5QTVWU05jM3YzWFBybjUxbUhrWDNXaFZlRjYwc1dsaDhR"


def get_gemini_key():
    try:
        return st.secrets["general"]["gemini_key"]
    except Exception:
        return base64.b64decode(ENCODED_GEMINI_KEY).decode("utf-8")


def safe_text(value):
    return str(value).encode("latin-1", "replace").decode("latin-1")


def create_pdf_report(data, invention_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, txt=safe_text(f"Patent Analysis Report: {invention_name}"), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, txt=safe_text(f"Novelty Score: {data.get('novelty_score', 'N/A')}%"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, txt=safe_text(f"Risk Level: {data.get('risk_level', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, txt=safe_text(f"TRL Estimate: {data.get('trl_level', 'N/A')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, txt="Detailed Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 8, txt=safe_text(data.get("analysis", "N/A")))

    return bytes(pdf.output())


def perform_advanced_analysis(invention_desc, gemini_key):
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    prompt = f'''
Return ONLY valid JSON:
{{
  "novelty_score": 85,
  "risk_level": "Low",
  "trl_level": "6",
  "analysis": "Analyze this invention in detail: {invention_desc}"
}}
'''
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(text)


st.title("🔍 Advanced Patent Novelty & Filing Suite")

invention_title = st.text_input("Invention Title")
invention_desc = st.text_area("Detailed Technical Description")

if st.button("Execute Analysis"):
    if not invention_desc.strip():
        st.warning("Please enter the invention description.")
    else:
        with st.spinner("Analyzing..."):
            gemini_key = get_gemini_key()
            result = perform_advanced_analysis(invention_desc, gemini_key)

        col1, col2, col3 = st.columns(3)
        col1.metric("Novelty Score", f"{result.get('novelty_score', 'N/A')}%")
        col2.metric("Risk Level", result.get("risk_level", "N/A"))
        col3.metric("TRL Level", result.get("trl_level", "N/A"))

        st.subheader("Analysis")
        st.write(result.get("analysis", "N/A"))

        pdf_data = create_pdf_report(result, invention_title or "Unnamed Invention")
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="patent_report.pdf",
            mime="application/pdf"
        )
