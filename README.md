# 📖 Story Teller AI 🎨
**An AI-powered creative engine that crafts vivid stories and paints their scenes using Multi-Agent Orchestration.**

## 🚀 Overview
This project is a sophisticated AI application that takes a simple user idea and transforms it into a complete narrative experience. It leverages a **Multi-Agent Workflow** to separate the concerns of storytelling and image prompt engineering, ensuring high-quality outputs for both text and visuals.

## 🛠️ Technical Stack
* **Orchestration**: Built with **LangGraph** to manage the state and routing between different AI agents.
* **LLM**: Powered by **Google Gemini 2.5 Flash** (Free Tier) for logical reasoning and creative writing.
* **Image Generation**: Integrates **Stable Diffusion XL** via Hugging Face Inference API.
* **UI/UX**: Interactive dashboard built with **Streamlit**.
* **Environment**: Managed with `python-dotenv` for secure API key handling.

## 🧠 System Architecture
The system follows an **Orchestrator-Worker** design pattern:
1.  **The Orchestrator**: Analyzes the current state and decides whether the next step is to write a story, generate an image, or finish the process.
2.  **The Story Writer**: A specialized agent focused on narrative flow and vivid descriptions.
3.  **The Image Agent**: Translates the story's essence into a technical prompt for the SDXL model.

## 📂 Project Structure
```text
├── app/
│   ├── main.py          # Streamlit Interface
│   └── pipeline.py      # LangGraph Logic & Agents
├── .env                 # API Keys (Gemini & HF) - [Not to be uploaded]
├── .gitignore           # Files to exclude from Git
├── requirements.txt     # Dependency List
└── README.md            # Project Documentation

⚙️ Installation & Setup
Clone the repository:
git clone [https://github.com/your-username/story-teller.git](https://github.com/your-username/story-teller.git)
cd story-teller

Install dependencies:
pip install -r requirements.txt

Configure Environment Variables:
Create a .env file in the root directory and add your keys:
Plaintext
GOOGLE_API_KEY=your_gemini_key_here
HF_TOKEN=your_huggingface_token_here


Run the application:
streamlit run app/main.py