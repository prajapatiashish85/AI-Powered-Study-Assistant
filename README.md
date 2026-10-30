# 🎓 AI Powered Study Assistant

## 📌 Overview

AI Powered Study Assistant is an AI-based learning platform built using Python and Streamlit. It helps students study more effectively by allowing them to upload PDF documents, ask questions using Retrieval-Augmented Generation (RAG), generate AI-powered quizzes, track their performance, identify weak topics, and create personalized study plans.

The application uses Google Gemini AI, LangChain, FAISS, HuggingFace Embeddings, and SQLite to provide an interactive and personalized learning experience.

## 🚀 Features

### 📚 PDF-Based AI Learning
- Upload PDF documents
- Extract and process PDF text
- Text chunking and embeddings
- FAISS-based semantic search
- AI Question Answering using Google Gemini
- Retrieved source information
- Chat History

### 📝 AI Quiz Generator
- Generate AI-powered quizzes
- Topic-based questions
- Automatic answer evaluation
- Score calculation
- Quiz attempt history

### 📊 Student Performance Analytics
- Track quiz performance
- View previous quiz attempts
- Analyze student progress
- Identify weak topics
- Personalized improvement recommendations

### 📅 Smart Study Planner
- Create personalized study plans
- Set exam name and exam date
- Add topics and daily study hours
- Generate study timetables
- Download study plans as CSV
- Save and view previous study plans

### ✅ Study Task Tracker
- Add study tasks
- Mark tasks as completed
- Track task completion progress

### 👤 Student Profile Management
- Save student profile information
- Load previously saved profile
- Persistent profile storage

## 🛠️ Technologies Used

- Python
- Streamlit
- Google Gemini API
- LangChain
- HuggingFace Embeddings
- FAISS Vector Database
- PyPDFLoader
- SQLite
- Pandas

## 📂 Project Structure

```text
AI-Powered-Study-Assistant/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── assets/
├── database/
│   └── db_manager.py
├── modules/
│   └── quiz_generator.py
└── vectorstore/
```

## ▶️ Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/prajapatiashish85/-AI-Powered-Study-Assistant.git
```

### 2. Open the project folder

```bash
cd -AI-Powered-Study-Assistant
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Gemini API Key

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key
```

Never upload your `.env` file or API key to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

## 🗄️ Database

SQLite is used to store:
- Quiz attempts and scores
- Study plans
- Study tasks
- Student profile information

## 🔐 Security

- API keys are stored in environment variables.
- Sensitive configuration files are excluded using `.gitignore`.
- Local database files are not uploaded to GitHub.

## 👨‍💻 Author

**Ashish Prajapati**

GitHub: https://github.com/prajapatiashish85