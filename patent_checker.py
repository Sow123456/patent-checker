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
    
    # Priority 1: Check for Shared/Master Key in Streamlit Secrets
    shared_key = st.secrets.get("general", {}).get("gemini_key", "")
    
    if shared_key:
        st.success("✅ Using Global Suite Key")
        gemini_key = shared_key
    else:
        st.info("No shared key found. Please provide your own.")
        gemini_key = st.text_input("Gemini API Key", type="password")
    
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
    
    # Try to load a Unicode-compatible font (Arial is standard on Windows)
    font_path = r"C:\Windows\Fonts\arial.ttf"
    bold_font_path = r"C:\Windows\Fonts\arialbd.ttf"
    
    if os.path.exists(font_path):
        pdf.add_font("ArialUnicode", "", font_path)
        if os.path.exists(bold_font_path):
            pdf.add_font("ArialUnicode", "B", bold_font_path)
        pdf.set_font("ArialUnicode", size=12)
        font_name = "ArialUnicode"
    else:
        pdf.set_font("Helvetica", size=12)
        font_name = "Helvetica"
        
    # Title
    pdf.set_font(font_name, 'B', 18)
    pdf.set_text_color(0, 123, 255)  # Professional Blue
    pdf.cell(190, 15, text="ADVANCED PATENT ANALYSIS REPORT", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.set_font(font_name, 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 10, text=f"Invention: {invention_name}", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    # Summary Table Headers
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font(font_name, 'B', 12)
    pdf.cell(63, 10, text="Novelty Score", border=1, align='C', fill=True)
    pdf.cell(63, 10, text="Risk Level", border=1, align='C', fill=True)
    pdf.cell(64, 10, text="TRL Level", border=1, align='C', fill=True)
    pdf.ln()
    
    # Summary Table Values
    pdf.set_font(font_name, '', 12)
    pdf.cell(63, 10, text=f"{data.get('novelty_score', 'N/A')}%", border=1, align='C')
    pdf.cell(63, 10, text=data.get('risk_level', 'N/A'), border=1, align='C')
    pdf.cell(64, 10, text=data.get('trl_level', 'N/A'), border=1, align='C')
    pdf.ln(15)
    
    # Sections
    sections = [
        ("EXECUTIVE ANALYSIS", data.get('analysis', 'N/A')),
        ("FILING RECOMMENDATIONS", data.get('filing_advice', 'N/A')),
        ("DRAFT CLAIMS (INITIAL)", data.get('draft_claims', 'N/A'))
    ]
    
    for title, content in sections:
        pdf.set_font(font_name, 'B', 14)
        pdf.set_text_color(0, 123, 255)
        pdf.cell(190, 10, text=title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font(font_name, '', 11)
        pdf.multi_cell(190, 6, text=content)
        pdf.ln(8)
        
    # Suggestions
    pdf.set_font(font_name, 'B', 14)
    pdf.set_text_color(0, 123, 255)
    pdf.cell(190, 10, text="IMPROVEMENT SUGGESTIONS", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, '', 11)
    suggestions = data.get('suggestions', [])
    if isinstance(suggestions, list):
        for s in suggestions:
            pdf.multi_cell(190, 6, text=f"- {s}")
    else:
        pdf.multi_cell(190, 6, text=str(suggestions))
    pdf.ln(8)
    
    # Similar Art
    pdf.set_font(font_name, 'B', 14)
    pdf.set_text_color(0, 123, 255)
    pdf.cell(190, 10, text="SIMILAR PRIOR ART IDENTIFIED", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font(font_name, '', 11)
    for art in data.get('similar_art', []):
        pdf.set_font(font_name, 'B', 11)
        pdf.multi_cell(190, 6, text=f"{art.get('title')} ({art.get('id')})")
        pdf.set_font(font_name, '', 10)
        pdf.multi_cell(190, 5, text=f"Source: {art.get('link')}")
        pdf.ln(3)
        
    return bytes(pdf.output())

# --- AI LOGIC ---
def perform_advanced_analysis(invention_desc, research_context, api_key, lang, dom, jurs):
    try:
        genai.configure(api_key=api_key)
        models = ['gemini-pro-latest', 'gemini-flash-lite-latest', 'gemini-2.0-flash-lite']
        
        jur_context = ", ".join(jurs) if jurs else "Global (Analyze and recommend most suitable jurisdictions)"
        
        for m_name in models:
            try:
                model = genai.GenerativeModel(m_name)
                prompt = f"""
                You are a Senior Patent Attorney and Technical Analyst specializing in {dom}.
                Analyze the following invention in {lang}.
                
                Invention: {invention_desc}
                Research Context: {research_context}
                Target Jurisdictions: {jur_context}
                
                Provide a comprehensive analysis including:
                1. Novelty Score (0-100)
                2. Risk Level (Low/Medium/High)
                3. TRL (Technology Readiness Level) Estimation (1-9)
                4. Analysis: Comparison with existing patents and research papers.
                5. Filing Advice: Specific recommendations for {jur_context}. If no specific jurisdictions were provided, suggest the top 3 countries/regions where this should be filed.
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
                    jur_display = ", ".join(jurisdiction) if jurisdiction else "Global Recommendations"
                    st.subheader(f"Jurisdiction Advice ({jur_display})")
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
                        # PDF Option (Primary)
                        try:
                            pdf_data = create_pdf_report(result, inv_title or "Unnamed Invention")
                            st.download_button(label="📕 Download Technical Report (PDF)", data=pdf_data, file_name=f"Patent_Report_{inv_title}.pdf", mime="application/pdf")
                        except Exception as e:
                            st.error(f"PDF Error: {e}")
                            st.info("Please use the TXT version below.")
                    
                    with col2:
                        # Text Option (Fallback/Alternative)
                        txt_data = create_txt_report(result, inv_title or "Unnamed Invention")
                        st.download_button(label="📄 Download Technical Report (TXT)", data=txt_data, file_name=f"Patent_Report_{inv_title}.txt", mime="text/plain")
                    
                    st.info("PDF format is recommended for professional use. TXT is provided for maximum compatibility.")
            else:
                st.error("Analysis failed. Please try again.")
