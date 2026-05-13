import base64
import json
import time
import streamlit as st
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, TooManyRequests, GoogleAPICallError
from fpdf import FPDF

st.set_page_config(page_title="Advanced Patent Suite", page_icon="🛡️", layout="wide")

ENCODED_GEMINI_KEY = "QUl6YVN5Q1pnUXlVVnR5d2NpZEhKNGpDS1h2NmRTSlZNV1dMc2xN"
MODEL_CANDIDATES = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]


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


def parse_json_response(text, invention_desc):
    cleaned = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "novelty_score": "N/A",
            "risk_level": "Unknown",
            "trl_level": "N/A",
            "analysis": cleaned or f"Unable to parse structured response for: {invention_desc[:500]}"
        }


def generate_with_retry(model, prompt, retries=2, delay=4):
    for attempt in range(retries + 1):
        try:
            return model.generate_content(prompt)
        except (ResourceExhausted, TooManyRequests):
            if attempt == retries:
                raise
            time.sleep(delay * (attempt + 1))


def perform_advanced_analysis(invention_desc, gemini_key):
    genai.configure(api_key=gemini_key)
    prompt = f'''
Return ONLY valid JSON:
{{
  "novelty_score": 85,
  "risk_level": "Low",
  "trl_level": "6",
  "analysis": "Analyze this invention in detail: {invention_desc}"
}}
'''

    last_error = None
    for model_name in MODEL_CANDIDATES:
        try:
            model = genai.GenerativeModel(model_name)
            response = generate_with_retry(model, prompt)
            return parse_json_response(response.text, invention_desc)
        except (ResourceExhausted, TooManyRequests, GoogleAPICallError) as exc:
            last_error = exc
            continue

    raise last_error if last_error else RuntimeError("Analysis failed")


st.title("🔍 Advanced Patent Novelty & Filing Suite")

invention_title = st.text_input("Invention Title")
invention_desc = st.text_area("Detailed Technical Description")

if st.button("Execute Analysis"):
    if not invention_desc.strip():
        st.warning("Please enter the invention description.")
    else:
        try:
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
        except ResourceExhausted:
            st.error("Gemini API quota has been exhausted for this key. Please wait and try again later, switch to a different API key, or upgrade the quota for the key in use.")
        except TooManyRequests:
            st.error("Too many requests were sent to Gemini in a short time. Please wait a moment and retry.")
        except Exception as exc:
            st.error(f"Analysis failed: {exc}")
