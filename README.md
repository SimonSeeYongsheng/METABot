
# 📘 METABot – An Educational Chatbot to Enhance Learning and Self-Efficacy

## 🧠 Overview

METABot is a Generative AI-powered chatbot designed to support tertiary education. It integrates:
- Learning content delivery using **ChatGPT-4o**
- Behaviour analysis through the **Felder-Silverman Learning Style Model (FSLSM)**
- **Misconception detection** based on chat history


## 🚀 Features

- 🤖 **Conversational Tutoring** — Delivers scaffolded content explanations
- 🔍 **Learning Style Analysis** — Analyzes chat patterns to infer student learning preferences
- ❌ **Misconception Reports** — Detects and explains conceptual misunderstandings
- 📚 **Document-based Q&A** — Retrieves relevant info from user-uploaded materials
- - 🗓️ **Daily Interaction Prompts** — Automatically sends questions to keep users engaged and support consistent learning
- 🧪 **Telegram Bot Integration** — Hosted on a public bot for experimentation

---

## 🧑‍💻 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/SimonSeeYongsheng/METABot.git
cd METABot
```
### 2. Install dependencies
```bash
pip install -r requirements.txt
```
### 3. Setup environment variables
Create a `.env` file in the root directory of the project and add your configuration variables in the following format:

```bash
export TELE_BOT_TOKEN="your-telegram-bot-token"
export GOOGLE_API_KEY="your-google-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export MONGO_URI="your-mongodb-uri"
export FILE_DRIVE="your-file-drive-path"
```
### 4. Run the bot
```bash
python TelegramBot.py
```

---

## 📌 Notes
This project was developed as part of a B.Sc. (Business Analytics) Final Year Project at NUS School of Computing.
