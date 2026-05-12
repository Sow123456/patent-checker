import streamlit as st
import google.generativeai as genai
import json
import os
from fpdf import FPDF

# --- PAGE CONFIG ---
st.set_page_config(page_title="Advanced Patent Suite", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    .report-box { padding: 20px; border-radius: 10px; background-color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .novelty-score { font-size: 48px; font-weight: bold; text-align: center; color: #007bff; }
    .patent-card { padding: 15px; border-left: 5px solid #28a745; background-color: #f8f9fa; margin-bottom: 10px; border-radius: 0 5px 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Suite Config")
    default_gemini = st.secrets.get("general", {}).get("gemini_key", "")
    gemini_key = st.text_input("Gemini API Key", value=default_gemini, type="password")
    
    st.markdown("---")
    language = st.selectbox("🌍 Analysis Language", ["English", "Hindi", "Spanish", "French", "German", "Chinese"])
    domain = st.selectbox("🏗️ Technology Domain", ["General", "Medical Devices", "IoT & Smart Systems", "AI & Software", "Electronics", "Biotechnology", "Mechanical"])
    jurisdiction = st.multiselect("⚖️ Target Jurisdictions", ["India", "USA", "PCT (International)"], default=["India"])
    
    st.info("Advanced Patent Suite v2.0")

# --- TEXT REPORT GENERATOR ---
def create_txt_report(data, invention_name):
    report = f"Patent Analysis Report: {invention_name}\n"
    report += "="*50 + "\n\n"
    report += f"Novelty Score: {data.get('novelty_score', 'N/A')}%\n"
    report += f"Risk Level: {data.get('risk_level', 'N/A')}\n"
    report += f"TRL Estimate: {data.get('trl_level', 'N/A')}\n"
    report += "-"*50 + "\n\n"
    
    report += "EXECUTIVE ANALYSIS:\n"
    report += data.get('analysis', 'N/A') + "\n\n"
    
    report += "FILING RECOMMENDATIONS:\n"
    report += data.get('filing_advice', 'N/A') + "\n\n"
    
    report += "DRAFT CLAIMS (INITIAL):\n"
    report += data.get('draft_claims', 'N/A') + "\n\n"
    
    report += "IMPROVEMENT SUGGESTIONS:\n"
    suggestions = data.get('suggestions', [])
    if isinstance(suggestions, list):
        for s in suggestions:
            report += f"- {s}\n"
    else:
        report += str(suggestions) + "\n"
        
    report += "\nSIMILAR PRIOR ART IDENTIFIED:\n"
    for art in data.get('similar_art', []):
        report += f"- {art.get('title')} ({art.get('id')}): {art.get('link')}\n"
        
    return report

# --- PDF REPORT GENERATOR ---
def create_pdf_report(data, invention_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Use standard fonts for Cloud compatibility
    pdf.set_font("Helvetica", size=12)
    font_name = "Helvetica"
        
    # Title
    pdf.set_font(font_name, 'B', 16)
    pdf.cell(190, 10, text=f"Patent Analysis Report: {invention_name}", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    # Metrics
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(190, 10, text=f"Novelty Score: {data.get('novelty_score', 'N/A')}%", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 10, text=f"Risk Level: {data.get('risk_level', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(190, 10, text=f"TRL Estimate: {data.get('trl_level', 'N/A')}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Sections
    sections = [
        ("EXECUTIVE ANALYSIS", data.get('analysis', 'N/A')),
        ("FILING RECOMMENDATIONS", data.get('filing_advice', 'N/A')),
        ("DRAFT CLAIMS (INITIAL)", data.get('draft_claims', 'N/A'))
    ]
    
    for title, content in sections:
        pdf.set_font(font_name, 'B', 12)
        pdf.cell(190, 10, text=title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font(font_name, '', 10)
        if font_name == "Helvetica":
            content = content.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 5, text=content)
        pdf.ln(5)
        
    # Suggestions
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(190, 10, text="IMPROVEMENT SUGGESTIONS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_name, '', 10)
    suggestions = data.get('suggestions', [])
    if isinstance(suggestions, list):
        for s in suggestions:
            if font_name == "Helvetica": s = s.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(190, 5, text=f"- {s}")
    else:
        s = str(suggestions)
        if font_name == "Helvetica": s = s.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 5, text=s)
    pdf.ln(5)
    
    # Similar Art
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(190, 10, text="SIMILAR PRIOR ART IDENTIFIED", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(font_name, '', 10)
    for art in data.get('similar_art', []):
        text = f"- {art.get('title')} ({art.get('id')}): {art.get('link')}"
        if font_name == "Helvetica": text = text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(190, 5, text=text)
        
    return bytes(pdf.output())

# --- AI LOGIC ---
def perform_advanced_analysis(invention_desc, research_context, api_key, lang, dom, jurs):
    try:
        genai.configure(api_key=api_key)
        models = ['gemini-pro-latest', 'gemini-flash-lite-latest', 'gemini-2.0-flash-lite']
        
        for m_name in models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                You are a Senior Patent Attorney and Technical Analyst specializing in {dom}.
                Analyze the following invention in {lang}.
                
                Invention: {invention_desc}
                Research Context: {research_context}
                Target Jurisdictions: {', '.join(jurs)}
                
                Provide a comprehensive analysis including:
                1. Novelty Score (0-100)
                2. Risk Level (Low/Medium/High)
                3. TRL (Technology Readiness Level) Estimation (1-9)
                4. Analysis: Comparison with existing patents and research papers.
                5. Filing Advice: Specific recommendations for {', '.join(jurs)}.
                6. Draft Claims: Generate 1 independent and 2 dependent claims.
                7. Suggestions: How to improve patentability.
                8. Similar Art: List of 3 relevant patents/papers with snippets and search links.
                
                Return ONLY a JSON response:
                {{
                  "novelty_score": int,
                  "risk_level": "string",
                  "trl_level": "string",
                  "analysis": "string",
                  "filing_advice": "string",
                  "draft_claims": "string",
                  "suggestions": ["string"],
                  "similar_art": [{{ "title": "string", "id": "string", "snippet": "string", "link": "string" }}]
                }}
                """
                response = model.generate_content(prompt)
                return json.loads(response.text.strip().replace('```json', '').replace('```', ''))
            except: continue
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- UI ---
st.title("🔍 Advanced Patent Novelty & Filing Suite")
st.markdown("Global prior art search, TRL estimation, claim drafting, and filing roadmap.")

col_a, col_b = st.columns(2)
with col_a:
    inv_title = st.text_input("Invention Title", placeholder="e.g., IoT-based Smart Irrigation Valve")
    inv_desc = st.text_area("Detailed Technical Description", height=250, placeholder="Explain the mechanics, logic, and novelty...")

with col_b:
    res_context = st.text_area("Research Context / Paper References (Optional)", height=325, placeholder="Paste snippets from related research papers or your own draft paper for combined analysis.")

if st.button("🛡️ Execute Comprehensive Analysis"):
    if not gemini_key or not inv_desc:
        st.warning("Please provide API key and invention description.")
    else:
        with st.spinner("Processing Global Databases..."):
            result = perform_advanced_analysis(inv_desc, res_context, gemini_key, language, domain, jurisdiction)
            
            if result:
                tabs = st.tabs(["📊 Novelty & TRL", "⚖️ Filing & Claims", "🔎 Prior Art", "📄 Report"])
                
                with tabs[0]:
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Novelty Score", f"{result['novelty_score']}%")
                    c2.metric("Risk Level", result['risk_level'])
                    c3.metric("TRL Level", result['trl_level'])
                    st.subheader("Technical Analysis")
                    st.write(result['analysis'])
                    
                with tabs[1]:
                    st.subheader(f"Jurisdiction Advice ({', '.join(jurisdiction)})")
                    st.write(result['filing_advice'])
                    st.subheader("Draft Claims")
                    st.code(result['draft_claims'], language='text')
                    st.subheader("Improvement Roadmap")
                    for s in result['suggestions']: st.write(f"✅ {s}")
                    
                with tabs[2]:
                    st.subheader("Identified Patents & Research Papers")
                    for art in result['similar_art']:
                        with st.container():
                            st.markdown(f"""<div class='patent-card'><strong>{art['title']}</strong> ({art['id']})<br/>{art['snippet']}<br/><a href='{art['link']}' target='_blank'>Source Link</a></div>""", unsafe_allow_html=True)
                            
                with tabs[3]:
                    st.subheader("Download Full Report")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        # Text Option (Always works)
                        txt_data = create_txt_report(result, inv_title or "Unnamed Invention")
                        st.download_button(label="📄 Download Technical Report (TXT)", data=txt_data, file_name=f"Patent_Report_{inv_title}.txt", mime="text/plain")
                    
                    with col2:
                        # PDF Option
                        try:
                            pdf_data = create_pdf_report(result, inv_title or "Unnamed Invention")
                            st.download_button(label="📕 Download Technical Report (PDF)", data=pdf_data, file_name=f"Patent_Report_{inv_title}.pdf", mime="application/pdf")
                        except Exception as e:
                            st.error(f"PDF Error: {e}")
                            st.info("Falling back to TXT report.")
                    
                    st.info("Report is provided in PDF and .txt formats. Use PDF for presentations and TXT for maximum compatibility.")
            else:
                st.error("Analysis failed. Please try again.")
