## 🏮 SkyWishes Portal
Bring your 2026 dreams to life among the stars.

SkyWishes is a creative sanctuary designed to help you slow down, reflect, and send your aspirations into the digital firmament. This project leverages the crewAI framework to coordinate a team of AI agents—the Wish Architect Crew—who work together to validate, refine, and transform your wishes into actionable roadmaps.

## ✨ Features
Celestial Narrative: A serene, interactive experience for releasing "Sky Lanterns".

Wish Architect Crew: Two specialized agents powered by Google Gemini models collaborate to ensure your wishes are both protected and planned for.

Action Roadmaps: Receive more than just a summary; get a structured Kanban-style plan to make your wish a reality.

Cross-Device Sync: Integrated with Supabase for secure user authentication and historical wish tracking.

Daily Rituals: Limited to 5 wishes per day to encourage intentionality and reflection.

## 🛠️ Tech Stack
Framework: crewAI (Multi-agent orchestration)

Frontend: Streamlit (Interactive web portal)

Intelligence: Google Gemini 2.5/3 Flash

Database: Supabase (Auth & History)

Deployment: Streamlit Cloud with GitHub Actions for 24/7 "Keep-Awake" automation.

## 🚀 Quick Start
Installation
Ensure you have Python ^3.10 and uv installed. This project uses uv for lightning-fast dependency management.

Bash

# Install uv if you haven't already
pip install uv

# Install project dependencies
uv sync
Configuration
Environment Variables: Create a .env file in the root directory:

Code snippet

GOOGLE_API_KEY=your_gemini_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
Agent Logic:

Modify src/my_project/config/agents.yaml to adjust the personalities of the Wish Guard and Wish Architect.

Edit src/my_project/crew.py to refine the collaborative logic.

Running Locally
Bash

streamlit run app.py
## 🧠 Understanding the Crew
The Wish Architect Crew operates through two primary agents:

The Wish Guard: Ensures every wish released into the sky is respectful and safe, acting as a gentle gatekeeper for the celestial portal.

The Wish Architect: A creative strategist that takes your dream and breaks it down into clear, achievable steps, providing a sense of direction and hope.

## 🌙 About the Creator
Hi, I’m Qiao (Joanna) 👋

I’m a Creative Technologist exploring the intersection of AI, arts, and narrative.

Portfolio: yiyueqiao.vercel.app
