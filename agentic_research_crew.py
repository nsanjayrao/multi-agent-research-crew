import streamlit as st
import os
import sys
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from fpdf import FPDF, XPos, YPos
from ddgs import DDGS

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

# The core PDF fonts (helvetica) only support latin-1, so common characters that
# LLMs emit -- em dashes, curly quotes, bullets -- would otherwise render as "?".
# Transliterate them to safe ASCII before writing.
_UNICODE_MAP = {
    "—": "-", "–": "-", "‒": "-", "―": "-",
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "…": "...", "•": "-", "‣": "-", "●": "-",
    " ": " ", "​": "", "→": "->", "←": "<-",
}

def _sanitize(text):
    for bad, good in _UNICODE_MAP.items():
        text = text.replace(bad, good)
    return text.encode("latin-1", "replace").decode("latin-1")

# PDF Generation Helper
def generate_pdf(text, title="Research Report"):
    pdf = FPDF()
    pdf.add_page()

    # Document Title Page Block
    pdf.set_font("helvetica", style="B", size=18)
    pdf.cell(0, 15, _sanitize(title.upper()), new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(10)

    # Parse Markdown lines and format headings beautifully in PDF
    lines = text.split("\n")
    for line in lines:
        if line.startswith("# "):
            # Main Heading
            pdf.ln(5)
            pdf.set_font("helvetica", style="B", size=15)
            pdf.cell(0, 10, _sanitize(line[2:].strip()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(2)
        elif line.startswith("## "):
            # Subheading
            pdf.ln(4)
            pdf.set_font("helvetica", style="B", size=13)
            pdf.cell(0, 10, _sanitize(line[3:].strip()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
        elif line.startswith("### "):
            # Smaller Subheading
            pdf.ln(3)
            pdf.set_font("helvetica", style="B", size=11)
            pdf.cell(0, 8, _sanitize(line[4:].strip()), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)
        elif line.startswith("* ") or line.startswith("- "):
            # Bullet points
            pdf.set_font("helvetica", size=10)
            clean_bullet = line[2:].strip().replace("**", "").replace("__", "").replace("*", "").replace("_", "")
            pdf.multi_cell(0, 6, text=f"  o {_sanitize(clean_bullet)}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        elif line.strip() == "":
            pdf.ln(2)
        else:
            # Standard Paragraph text
            pdf.set_font("helvetica", size=10)
            clean_line = line.replace("**", "").replace("__", "").replace("*", "").replace("_", "")
            pdf.multi_cell(0, 6, text=_sanitize(clean_line), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

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
        
    st.header("⚙️ Settings")

    # gemini-3.1-flash-lite is the default because a single crew run makes 10-20+
    # LLM calls, and the free tier caps gemini-3.5-flash at only 20 requests/DAY --
    # one run can exhaust it. Flash-lite has a far higher daily quota.
    model_choice = st.selectbox(
        "Gemini Model",
        options=["gemini-3.1-flash-lite", "gemini-3.5-flash"],
        index=0,
        help="flash-lite: high free-tier quota, ideal for demos. 3.5-flash: smartest, but free tier allows only ~20 requests/day (one crew run uses most of it)."
    )
    if model_choice == "gemini-3.5-flash":
        st.caption("⚠️ Free tier: ~20 requests/day on this model. A single crew run may hit the cap.")

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
            <strong>Goal:</strong> Uncover cutting-edge developments, insights, and factual data.<br>
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
    # CRITICAL SECURITY FIX: Explicitly set Gemini API keys in the environment.
    # CrewAI / LiteLLM looks for environment variables when calling sub-processes and tool tools.
    # Without these environment variables, LiteLLM falls back to OpenAI and throws 401 errors.
    os.environ["GEMINI_API_KEY"] = gemini_key
    os.environ["GOOGLE_API_KEY"] = gemini_key
    
    # Disable telemetry and tracing to prevent unnecessary network calls/errors
    os.environ["OTEL_SDK_DISABLED"] = "true"
    
    # Initialize the LLM. Route through LiteLLM (is_litellm=True) rather than
    # CrewAI's native Gemini provider: Gemini flash models frequently return transient
    # 503 "high demand" errors, and only the LiteLLM path retries them. Without this,
    # a single 503 on any agent call aborts the whole crew run.
    gemini_llm = LLM(
        model=f"gemini/{model_choice}",
        api_key=gemini_key,
        temperature=0.7,
        is_litellm=True,
        timeout=120,
        additional_params={"num_retries": 5},
    )
    
    # Offline fallback knowledge base -- used only if live search is unavailable
    # (no network, rate limiting) so a demo never hard-fails.
    def _mock_fallback(query: str) -> str:
        normalized_query = query.lower().strip()
        knowledge_base = {
            "agentic ai": "- Agentic AI is the dominant trend in 2026, transitioning from simple chatbots to autonomous multi-agent workflows.\n- Agents possess reasoning loops (ReAct), memory, and tool-use capabilities.\n- Moving away from single-agent chats toward collaborative, specialized multi-agent 'crews'.",
            "multi-agent orchestration": "- CrewAI is popular for role-playing, sequential, and hierarchical agentic workflows.\n- LangGraph excels in complex, cyclic graph-based agents and stateful, multi-turn control flows.\n- Key enterprise use cases include support audits and copywriting pipelines.",
            "generative ai trends 2026": "- Small, specialized open-weights LLMs are preferred for local, cost-effective deployments.\n- Enterprise focus has shifted to reliable, high-accuracy RAG pipelines (hybrid search and cross-encoder reranking)."
        }
        for key, value in knowledge_base.items():
            if key in normalized_query:
                return value
        return f"[Offline fallback] No live results for '{query}'. AI agents represent a major shift in software engineering, moving from deterministic logic to autonomous decision loops."

    # Real Web Search Tool -- DuckDuckGo, no API key required, works on Streamlit Cloud.
    @tool("Web Search Tool")
    def web_search_tool(query: str) -> str:
        """Search the live web for current information on a query and return the top results with sources."""
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=6))
            if not hits:
                return _mock_fallback(query)
            return "\n\n".join(
                f"- {h.get('title', '').strip()}\n  {h.get('body', '').strip()}\n  Source: {h.get('href', '').strip()}"
                for h in hits
            )
        except Exception:
            # Network failure or rate limit -- degrade gracefully instead of crashing the crew.
            return _mock_fallback(query)

    st.markdown("---")

    # Topic input lives on the main page (mirroring the RAG chatbot's design):
    # a centered form with a wide input and full-width submit. In the sidebar it
    # was invisible to anyone on a phone or with the sidebar collapsed.
    st.subheader("🔬 What should the crew research?")
    with st.form("kickoff_form"):
        topic = st.text_input(
            "Research topic",
            label_visibility="collapsed",
            placeholder="Enter any topic — e.g. Agentic AI, EV battery tech, AI in Indian healthcare…",
        )
        kickoff = st.form_submit_button("🚀 Kickoff Agentic Workflow", type="primary", use_container_width=True)

    if kickoff and not topic.strip():
        st.warning("⌨️ Type a topic in the box above, then kick off the workflow.")

    if kickoff and topic.strip():
        topic = topic.strip()
        # Interactive Step-by-Step Collaboration Statuses
        status_box = st.empty()

        with status_box.container():
            st.markdown("### ⚙️ Live Collaboration Tracker")
            p_research = st.status("🔍 Step 1: Principal Research Analyst is collecting data...", expanded=True)
            p_write = st.status("✍️ Step 2: Senior Technical Writer is drafting the article...", expanded=False)
            p_edit = st.status("🛡️ Step 3: Lead Editorial Director is fact-checking...", expanded=False)

        # The tracker advances only as each task genuinely finishes. CrewAI calls
        # task_callback after every completed task, in sequential order, so we walk
        # the phases one step at a time -- no more faking completion before kickoff.
        phases = [
            (p_research, "🔍 Step 1: Research Phase Completed!"),
            (p_write, "✍️ Step 2: Writing Phase Completed!"),
            (p_edit, "🛡️ Step 3: Editorial Phase Completed!"),
        ]
        phase_index = {"i": 0}

        def on_task_complete(task_output):
            i = phase_index["i"]
            if i < len(phases):
                phases[i][0].update(state="complete", label=phases[i][1])
                phase_index["i"] = i + 1
            # Open the next phase so the user sees it start working.
            if phase_index["i"] < len(phases):
                phases[phase_index["i"]][0].update(expanded=True)

        try:
            p_research.write("Searching the live web for relevant evidence...")

            # Define Agents
            researcher = Agent(
                role="Principal Research Analyst",
                goal=f"Uncover cutting-edge developments, structured insights, and factual data on the topic: {topic}",
                backstory="You are a meticulous researcher with a passion for emerging technologies and structured summaries.",
                tools=[web_search_tool],
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
                description=f"Conduct a detailed research investigation on the topic: {topic}. Use your Web Search Tool to gather current findings and compile a brief. Include the source URLs for the facts you report.",
                expected_output="A structured, bulleted research brief containing at least 5 major factual insights, each with its source URL.",
                agent=researcher
            )
            write_task = Task(
                description="Review the research brief and write a comprehensive, professional article in Markdown with headings and a forward-looking summary. Preserve the key facts and their sources from the brief.",
                expected_output="A full, engaging markdown article based on the research brief.",
                agent=writer
            )
            edit_task = Task(
                description="Review the writer's draft, verify that all claims are grounded in the research brief, polish the language, and output final publication-ready markdown.",
                expected_output="The final, publication-ready markdown article.",
                agent=editor
            )

            # Assemble Crew -- task_callback drives the honest progress tracker.
            crew = Crew(
                agents=[researcher, writer, editor],
                tasks=[research_task, write_task, edit_task],
                process=Process.sequential,
                task_callback=on_task_complete,
                verbose=True
            )

            # Execute Crew kickoff (Run the sequential process). This blocks until
            # all three agents finish; the tracker updates from on_task_complete.
            result = crew.kickoff(inputs={"topic": topic})
            status_box.empty()  # Clear statuses once complete to show clean results

            # Persist across reruns so the article survives the PDF download click.
            st.session_state["article"] = result.raw
            st.session_state["article_topic"] = topic

        except Exception as e:
            status_box.empty()
            err_text = str(e)
            if "429" in err_text or "RESOURCE_EXHAUSTED" in err_text or "quota" in err_text.lower():
                st.error(
                    "🚦 Gemini free-tier quota exceeded for this model today. "
                    "Switch the sidebar model to **gemini-3.1-flash-lite** (much higher daily limit) "
                    "or try again tomorrow. Details: rate limits reset daily per model."
                )
            elif "503" in err_text or "UNAVAILABLE" in err_text:
                st.error(
                    "⏳ Gemini is under heavy load right now and retries were exhausted. "
                    "Wait a minute and kick off the workflow again."
                )
            else:
                st.error(f"Error running the agentic workflow: {e}")

    # Render results from session state. Kept OUTSIDE the button block so it also
    # renders on the rerun triggered by clicking the PDF download button --
    # otherwise the finished article would vanish the moment the user downloads it.
    if st.session_state.get("article"):
        article = st.session_state["article"]
        article_topic = st.session_state.get("article_topic", "Research Report")

        st.success("🏆 Editorial Director has approved and published the final article!")

        with st.spinner("📄 Rendering high-quality PDF report..."):
            pdf_data = generate_pdf(article, title=article_topic)

        st.markdown("### 🏆 Final Publication-Ready Article")
        st.markdown(article)

        st.download_button(
            label="📥 Export Article as PDF",
            data=pdf_data,
            file_name=f"{article_topic.lower().replace(' ', '_')}_report.pdf",
            mime="application/pdf"
        )