# 👥 Autonomous Research & Editorial Crew

An autonomous multi-agent web dashboard built using the **CrewAI** and **Streamlit** frameworks. It orchestrates a collaborative, sequential workflow between three specialized AI agents (Researcher, Writer, and Editor) to research, draft, and publish professional reports, exporting them directly as **PDF documents**.

This project is designed as a portfolio-ready demonstration of **Agentic AI**—the most requested and valuable skillset in modern Generative AI engineering.

---

## 👥 The Agent Team
The system coordinates three autonomous agents:
1. **Principal Research Analyst (Researcher):** Searches the web (via a custom mockup tool) to gather structured insights, key facts, and verified data.
2. **Senior Technical Writer (Writer):** Takes the structured research brief and synthesizes it into a beautifully formatted markdown article with headings, an introduction, and a forward-looking summary.
3. **Lead Editorial Director (Editor):** Reviews the writer's draft to ensure it is strictly grounded in the research analyst's facts (preventing hallucinations), polishes the language, and formatting to deliver a publication-ready final output.

---

## 🛠️ Technology Stack
* **Orchestration Framework:** [CrewAI](https://docs.crewai.com/)
* **Dashboard Interface:** [Streamlit](https://streamlit.io/)
* **Document Generation:** [fpdf2](https://fpdf2.github.io/fpdf2/) (for direct PDF formatting and exporting)
* **AI Brain (LLM):** Google Gemini 1.5 Flash (via native LiteLLM integrations)
* **Custom Tools:** Pure-Python Mock Search Tool (fully runnable locally and offline without external API keys!)

---

## 🚀 How to Run the App Locally

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your computer.

### 2. Install Dependencies
```bash
pip install -r requirements_agents.txt
```

### 3. Run the Application
1. Start the Streamlit app:
   ```bash
   streamlit run agentic_research_crew.py
   ```
2. A browser tab will open automatically at `http://localhost:8501`.
3. Add your Gemini API Key in the sidebar, input any topic, and click **🚀 Kickoff Agentic Workflow** to watch your agents collaborate and publish your finished article!

---

## 🌐 Free Cloud Deployment

You can deploy this Agentic dashboard for free on **Streamlit Community Cloud**:
1. Push this folder to a new GitHub repository on your account.
2. Go to [Streamlit Share](https://share.streamlit.io/) and log in with GitHub.
3. Click **New App**, select your repository, branch (`main`), and set the Main file path to `agentic_research_crew.py`.
4. Click **Advanced Settings** > **Secrets**, and add your API key in TOML format:
   ```toml
   GEMINI_API_KEY = "your_actual_api_key_here"
   ```
5. Click **Deploy**—your Autonomous AI Agent Crew will be live on a public URL in minutes!

---

## 📄 License
This project is licensed under the MIT License.