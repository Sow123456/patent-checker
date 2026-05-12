import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

st.set_page_config(page_title="Advanced Patent Suite", page_icon="🛡️", layout="wide")

# Load Gemini API key from Streamlit secrets automatically
gemini_key = st.secrets["general"]["gemini_key"]

def create_txt_report(data, invention_name):
    report = f"Patent Analysis Report: {invention_name}\n"
    report += "="*50 + "\n\n"
    report += f"Novelty Score: {data.get('novelty_score', 'N/A')}%\n"
    report += f"Risk Level: {data.get('risk_level', 'N/A')}\n"
    report += f"TRL Estimate: {data.get('trl_level', 'N/A')}\n\n"
    report += data.get('analysis', 'N/A')
    return report

def create_pdf_report(data, invention_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, txt=f"Patent Analysis Report: {invention_name}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 8, txt=data.get("analysis", "N/A"))
    return pdf.output(dest="S").encode("latin-1")

def perform_advanced_analysis(invention_desc):
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    prompt = f'''
Return ONLY JSON:
{{
  "novelty_score": 85,
  "risk_level": "Low",
  "trl_level": "6",
  "analysis": "Analyze this invention: {invention_desc}"
}}
'''
    response = model.generate_content(prompt)
    text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(text)

st.title("🔍 Advanced Patent Novelty & Filing Suite")

title = st.text_input("Invention Title")
desc = st.text_area("Detailed Technical Description")

if st.button("Execute Analysis"):
    if not desc:
        st.warning("Please enter the invention description.")
    else:
        with st.spinner("Analyzing..."):
            result = perform_advanced_analysis(desc)
        st.metric("Novelty Score", f"{result['novelty_score']}%")
        st.metric("Risk Level", result["risk_level"])
        st.metric("TRL Level", result["trl_level"])
        st.write(result["analysis"])

        txt_data = create_txt_report(result, title or "Unnamed Invention")
        st.download_button(
            "Download TXT Report",
            data=txt_data,
            file_name="patent_report.txt",
            mime="text/plain"
        )

        pdf_data = create_pdf_report(result, title or "Unnamed Invention")
        st.download_button(
            "Download PDF Report",
            data=pdf_data,
            file_name="patent_report.pdf",
            mime="application/pdf"
        )
