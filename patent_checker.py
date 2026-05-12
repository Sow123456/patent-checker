import streamlit as st
import google.generativeai as genai
import json
from fpdf import FPDF

st.set_page_config(page_title="Advanced Patent Suite", page_icon="🛡️", layout="wide")

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Suite Config")

    default_gemini = st.secrets.get("general", {}).get("gemini_key", "")
    gemini_key = st.text_input(
        "Gemini API Key",
        value=default_gemini,
        type="password",
        help="Enter your Gemini API key only if it is not configured in Streamlit Secrets."
    )

    st.markdown("---")
    language = st.selectbox(
        "🌍 Analysis Language",
        ["English", "Hindi", "Spanish", "French", "German", "Chinese"]
    )
    domain = st.selectbox(
        "🏗️ Technology Domain",
        [
            "General",
            "Medical Devices",
            "IoT & Smart Systems",
            "AI & Software",
            "Electronics",
            "Biotechnology",
            "Mechanical"
        ]
    )
    jurisdiction = st.multiselect(
        "⚖️ Target Jurisdictions",
        ["India", "USA", "PCT (International)"],
        default=["India"]
    )

    st.info("Advanced Patent Suite v2.0")

def create_txt_report(data, invention_name):
    report = f"Patent Analysis Report: {invention_name}\n"
    report += "=" * 50 + "\n\n"
    report += f"Novelty Score: {data.get('novelty_score', 'N/A')}%\n"
    report += f"Risk Level: {data.get('risk_level', 'N/A')}\n"
    report += f"TRL Estimate: {data.get('trl_level', 'N/A')}\n\n"
    report += data.get("analysis", "N/A")
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

def perform_advanced_analysis(invention_desc, api_key):
    genai.configure(api_key=api_key)
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
st.markdown("Global prior art search, TRL estimation, claim drafting, and filing roadmap.")

title = st.text_input("Invention Title")
desc = st.text_area("Detailed Technical Description", height=250)

if st.button("🛡️ Execute Comprehensive Analysis"):
    if not gemini_key or not desc:
        st.warning("Please provide API key and invention description.")
    else:
        with st.spinner("Processing..."):
            result = perform_advanced_analysis(desc, gemini_key)

        st.metric("Novelty Score", f"{result['novelty_score']}%")
        st.metric("Risk Level", result["risk_level"])
        st.metric("TRL Level", result["trl_level"])
        st.write(result["analysis"])

        txt_data = create_txt_report(result, title or "Unnamed Invention")
        st.download_button(
            "📄 Download Technical Report (TXT)",
            data=txt_data,
            file_name="patent_report.txt",
            mime="text/plain"
        )

        pdf_data = create_pdf_report(result, title or "Unnamed Invention")
        st.download_button(
            "📕 Download Technical Report (PDF)",
            data=pdf_data,
            file_name="patent_report.pdf",
            mime="application/pdf"
        )
