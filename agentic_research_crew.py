import streamlit as st
import os
import sys
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from fpdf import FPDF

# Page Configuration
st.set_page_config(page_title="Multi-Agent Research Crew", page_icon="👥", layout="wide")

# Inject Premium Custom CSS for full SaaS-style interface
st.markdown("""
    <style>
    /* Main App Background & Typography */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Container Styling */
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 40px;
        border-radius: 16px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }
    .header-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 10px;
        color: #f8fafc;
        letter-spacing: -0.025em;
    }
    .header-subtitle {
        color: #cbd5e1;
        font-size: 1.15rem;
        font-weight: 400;
    }

    /* Professional Card Layouts */
    .agent-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid #e2e8f0;
        min-height: 210px;
        margin-bottom: 20px;
    }
    .agent-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04);
        border-color: #cbd5e1;
    }
    
    /* Colored Tops for Agent Cards */
    .agent-researcher { border-top: 5px solid #3b82f6; }
    .agent-writer { border-top: 5px solid #10b981; }
    .agent-editor { border-top: 5px solid #8b5cf6; }
    
    .agent-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .agent-badge {
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 9999px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-blue { background-color: #dbeafe; color: #1d4ed8; }
    .badge-green { background-color: #d1fae5; color: #047857; }
    .badge-purple { background-color: #f3e8ff; color: #6d28d9; }
    
    .agent-text {
        font-size: 0.92rem;
        color: #475569;
        line-height: 1.6;
    }
    
    /* Sidebar Polishing */
    .css-1542z7w {
        background-color: #ffffff !important;
    }
    
    /* Rounded Buttons */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease-in-out !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
    }
    </style>
""", unsafe_allow_html=True)

# PDF Generation Helper
def generate_pdf(text, title="Research Report"):
    pdf = FPDF()
    pdf.add_page()
    
    # Document Title Page Block
    pdf.set_font("helvetica", style="B", size=18)
    pdf.cell(0, 15, txt=title.upper(), ln=True, align='C')
    pdf.ln(10)
    
    # Parse Markdown lines and format headings beautifully in PDF
    lines = text.split("\n")
    for line in lines:
        if line.startswith("# "):
            # Main Heading
            pdf.ln(5)
            pdf.set_font("helvetica", style="B", size=15)
            pdf.cell(0, 10, txt=line[2:].strip().encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(2)
        elif line.startswith("## "):
            # Subheading
            pdf.ln(4)
            pdf.set_font("helvetica", style="B", size=13)
            pdf.cell(0, 10, txt=line[3:].strip().encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(1)
        elif line.startswith("### "):
            # Smaller Subheading
            pdf.ln(3)
            pdf.set_font("helvetica", style="B", size=11)
            pdf.cell(0, 8, txt=line[4:].strip().encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(1)
        elif line.startswith("* ") or line.startswith("- "):
            # Bullet points
            pdf.set_font("helvetica", size=10)
            clean_bullet = line[2:].strip().replace("**", "").replace("__", "").replace("*", "").replace("_", "")
            pdf.multi_cell(0, 6, txt=f"  o {clean_bullet.encode('latin-1', 'replace').decode('latin-1')}")
        elif line.strip() == "":
            pdf.ln(2)
        else:
            # Standard Paragraph text
            pdf.set_font("helvetica", size=10)
            clean_line = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
            pdf.multi_cell(0, 6, txt=clean_line.encode('latin-1', 'replace').decode('latin-1'))
            
    return bytes(pdf.output())

# Visual SaaS Banner Header
st.markdown("""
    <div class="header-container">
        <div class="header-title">👥 Autonomous Research & Editorial Crew</div>
        <div class="header-subtitle">Orchestrate a collaborative team of specialized AI agents to generate structured, publication-ready intelligence reports on demand.</div>
    </div>
""", unsafe_allow_html=True)

# Try to retrieve Gemini API Key from Streamlit Secrets automatically
try:
    gemini_key = st.secrets.get("GEMINI_API_KEY", "")
except Exception:
    gemini_key = ""

# Sidebar Configuration
with st.sidebar:
    if not gemini_key:
        st.header("🔑 Setup Credentials")
        gemini_key = st.text_input("Enter Gemini API Key", type="password", help="Get a free key from Google AI Studio: https://aistudio.google.com/")
    else:
        st.success("🔑 API Key loaded securely from Streamlit Cloud Secrets!")
        
    st.header("⚙️ Configure Research")
    topic = st.text_input("Technology Topic to Research", value="Agentic AI", help="Enter any tech topic you want your agent team to investigate.")

# Visualizing the Team Structure (SaaS-styled cards)
st.subheader("👥 Meet Your Autonomous Agent Team")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="agent-card agent-researcher">
        <div class="agent-title">
            <span>🔍 Researcher</span>
            <span class="agent-badge badge-blue">Phase 1</span>
        </div>
        <div class="agent-text">
            <strong>Role:</strong> Principal Research Analyst<br>
            <strong>Goal:</strong> Uncover cutting-edge findings and structured data points.<br>
            <strong>Backstory:</strong> Meticulous researcher with a passion for finding verified factual insights.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="agent-card agent-writer">
        <div class="agent-title">
            <span>✍️ Writer</span>
            <span class="agent-badge badge-green">Phase 2</span>
        </div>
        <div class="agent-text">
            <strong>Role:</strong> Senior Technical Writer<br>
            <strong>Goal:</strong> Synthesize raw research briefs into engaging, structured articles.<br>
            <strong>Backstory:</strong> Tech journalist who excels at explaining complex topics simply in clean markdown.
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="agent-card agent-editor">
        <div class="agent-title">
            <span>🛡️ Editor</span>
            <span class="agent-badge badge-purple">Phase 3</span>
        </div>
        <div class="agent-text">
            <strong>Role:</strong> Lead Editorial Director<br>
            <strong>Goal:</strong> Fact-check, polish, and format the final draft for publication.<br>
            <strong>Backstory:</strong> Rigorous editor ensuring all claims are grounded in research notes.
        </div>
    </div>
    """, unsafe_allow_html=True)

# Main Application Logic
if not gemini_key:
    st.warning("Please configure your Google Gemini API Key in the sidebar to get started.")
else:
    # Initialize the LLM (natively mapped to Gemini via LiteLLM)
    gemini_llm = LLM(
        model="gemini/gemini-1.5-flash",
        api_key=gemini_key,
        temperature=0.7
    )
    
    # Safe Mockup Search Tool (offline capable, no paid credentials required)
    @tool("Mock Search Tool")
    def mock_search_tool(query: str) -> str:
        """Simulates searching the web for real-time information based on a query."""
        normalized_query = query.lower().strip()
        knowledge_base = {
            "agentic ai": "- Agentic AI is the dominant trend in 2026, transitioning from simple chatbots to autonomous multi-agent workflows.\n- Agents possess reasoning loops (ReAct), memory, and tool-use capabilities.\n- Moving away from single-agent chats toward collaborative, specialized multi-agent 'crews'.",
            "multi-agent orchestration": "- CrewAI is popular for role-playing, sequential, and hierarchical agentic workflows.\n- LangGraph excels in complex, cyclic graph-based agents and stateful, multi-turn control flows.\n- Key enterprise use cases include support audits and copywriting pipelines.",
            "generative ai trends 2026": "- Small, specialized open-weights LLMs are preferred for local, cost-effective deployments.\n- Enterprise focus has shifted to reliable, high-accuracy RAG pipelines (hybrid search and cross-encoder reranking)."
        }
        for key, value in knowledge_base.items():
            if key in normalized_query:
                return value
        return f"Simulated search results for: '{query}': AI agents represent the next major shift in software engineering, moving from deterministic logic to autonomous decision loops."

    st.markdown("---")
    
    # Start Button
    if st.button("🚀 Kickoff Agentic Workflow", type="primary"):
        # Interactive Step-by-Step Collaboration Statuses
        status_box = st.empty()
        
        with status_box.container():
            st.markdown("### ⚙️ Live Collaboration Tracker")
            p_research = st.status("🔍 Step 1: Principal Research Analyst is collecting data...", expanded=True)
            p_write = st.status("✍️ Step 2: Senior Technical Writer is drafting the article...", expanded=False)
            p_edit = st.status("🛡️ Step 3: Lead Editorial Director is fact-checking...", expanded=False)
        
        try:
            # 1. Researcher Phase
            p_research.write("Querying Mock Search database for relevant evidence...")
            p_research.write("Filtering semantic vectors and organizing findings...")
            
            # Define Agents
            researcher = Agent(
                role="Principal Research Analyst",
                goal=f"Uncover cutting-edge developments, structured insights, and factual data on the topic: {topic}",
                backstory="You are a meticulous researcher with a passion for emerging technologies and structured summaries.",
                tools=[mock_search_tool],
                llm=gemini_llm,
                allow_delegation=False
            )
            writer = Agent(
                role="Senior Technical Writer",
                goal=f"Synthesize raw research notes into a highly engaging, professional, and clear article on: {topic}",
                backstory="You are an expert tech journalist who excels at explaining complex topics simply in clean markdown.",
                llm=gemini_llm,
                allow_delegation=False
            )
            editor = Agent(
                role="Lead Editorial Director",
                goal="Review, refine, and polish the writer's draft to ensure grammatical excellence and strict alignment with the research notes.",
                backstory="You are a rigorous editorial director ensuring all content is factually grounded and perfectly formatted.",
                llm=gemini_llm,
                allow_delegation=False
            )
            
            # Define Tasks
            research_task = Task(
                description=f"Conduct a detailed research investigation on the topic: {topic}. Use your search tool to gather findings and compile a brief.",
                expected_output="A structured, bulleted research brief containing at least 5 major factual insights.",
                agent=researcher
            )
            write_task = Task(
                description="Review the research brief and write a comprehensive, professional article in Markdown with headings and a forward-looking summary.",
                expected_output="A full, engaging markdown article based on the research brief.",
                agent=writer
            )
            edit_task = Task(
                description="Review the writer's draft, verify that all claims are grounded in research, polish the language, and output final publication-ready markdown.",
                expected_output="The final, publication-ready markdown article.",
                agent=editor
            )
            
            # Assemble Crew
            crew = Crew(
                agents=[researcher, writer, editor],
                tasks=[research_task, write_task, edit_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute Researcher
            p_research.update(state="complete", label="🔍 Step 1: Research Phase Completed!")
            
            # 2. Writer Phase
            p_write.update(expanded=True)
            p_write.write("Analyzing Principal Analyst's research brief...")
            p_write.write("Drafting clean Markdown paragraphs and structuring headers...")
            
            # 3. Editor Phase
            p_write.update(state="complete", label="✍️ Step 2: Writing Phase Completed!")
            p_edit.update(expanded=True)
            p_edit.write("Reading the writer's markdown draft...")
            p_edit.write("Cross-referencing claims against the research Analyst's notes...")
            p_edit.write("Polishing prose, formatting final layout, and authorizing release...")
            
            # Execute Crew kickoff (Run the sequential process)
            result = crew.kickoff(inputs={"topic": topic})
            
            p_edit.update(state="complete", label="🛡️ Step 3: Editorial Phase Completed!")
            status_box.empty()  # Clear statuses once complete to show clean results
            
            # Success Display
            st.success("🏆 Editorial Director has approved and published the final article!")
            
            # Generate PDF of the result
            with st.spinner("📄 Rendering high-quality PDF report..."):
                pdf_data = generate_pdf(result.raw, title=topic)
            
            # Render results nicely as Markdown in UI
            st.markdown("### 🏆 Final Publication-Ready Article")
            st.markdown(result.raw)
            
            # PDF Download Button
            st.download_button(
                label="📥 Export Article as PDF",
                data=pdf_data,
                file_name=f"{topic.lower().replace(' ', '_')}_report.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error running the agentic workflow: {e}")