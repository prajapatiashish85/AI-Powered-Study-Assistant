
import streamlit as st
import tempfile
import time
import os
from pathlib import Path
from dotenv import load_dotenv

from google import genai
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🎓",
    layout="wide"
)

# Load .env from the same folder as app.py
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)

api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    st.success("Gemini API key loaded successfully.")
else:
    st.error("Gemini API key not found.")
    st.caption(f"Checking .env file at: {ENV_PATH}")


from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from modules.quiz_generator import generate_quiz
from database.db_manager import (
    initialize_database,
    save_quiz_attempt,
    get_quiz_history,
    initialize_study_plan_table,
    save_study_plan,
    get_study_plans,
    initialize_study_tasks_table,
    add_study_task,
    get_study_tasks,
    update_study_task,
    initialize_student_profile_table,
    save_student_profile,
    get_student_profile
)

initialize_database()
initialize_study_plan_table()
initialize_study_tasks_table()
initialize_student_profile_table()

# ---------------------------------------
# SESSION STATE
# ---------------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []



with st.sidebar:
    st.title("🎓 AI Study Assistant")
    st.markdown("---")

    st.subheader("📌 Features")

    features = [
        "📚 PDF Upload & AI Question Answering",
        "🔍 RAG & FAISS Search",
        "📝 AI Quiz Generator",
        "📊 Performance Analytics",
        "🎯 Weak Topic Detection",
        "📅 Smart Study Planner",
        "✅ Study Task Tracker",
        "👤 Student Profile Management",
        "💾 Quiz & Study History"
    ]

    for feature in features:
        st.success(f"✔ {feature}")

    st.markdown("---")

    st.info("""
    **Built with:**

    • Python
    • Streamlit
    • Google Gemini AI
    • LangChain
    • HuggingFace
    • FAISS
    • SQLite
    """)

    if st.button("🗑 Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()


# ---------------------------------------
# MAIN HEADING
# ---------------------------------------

st.title("🎓 AI Powered Study Assistant")

st.caption(
    "Upload your study material and ask questions using AI-powered retrieval."
)

st.write(
    "Upload your PDF and ask questions using Gemini AI."
)

st.divider()



# ---------------------------------------
# GEMINI API
# ---------------------------------------

client = None

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        st.success("Gemini client initialized successfully.")

    except Exception as e:
        st.error("Gemini initialization failed.")
        st.caption(str(e))
        client = None

else:
    st.error("Gemini API key not found.")


# ---------------------------------------
# PDF UPLOAD
# ---------------------------------------

uploaded_file = st.file_uploader(
    "Upload PDF",
    type=["pdf"]
)

vector_db = None
documents = []
chunks = []
full_text = ""


# ---------------------------------------
# LOAD AND PROCESS PDF
# ---------------------------------------

if uploaded_file:

    st.info(
        f"📄 Uploaded file: {uploaded_file.name}"
    )

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(uploaded_file.getvalue())
        pdf_path = temp_file.name

    try:
        with st.spinner("Reading PDF..."):
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()

        st.success("✅ PDF Loaded Successfully")

        for page in documents:
            full_text += page.page_content + "\n"

        if not full_text.strip():
            st.error(
                "PDF me readable text nahi mila."
            )

        else:
            # ---------------------------------------
            # TEXT CHUNKING
            # ---------------------------------------

            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )

            chunks = splitter.split_text(full_text)

            # ---------------------------------------
            # EMBEDDINGS AND FAISS
            # ---------------------------------------

            with st.spinner(
                "Creating embeddings and FAISS database..."
            ):
                embedding_model = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-small-en-v1.5"
                )

                vector_db = FAISS.from_texts(
                    texts=chunks,
                    embedding=embedding_model
                )

            st.success(
                "✅ FAISS Vector Database Ready"
            )

            # ---------------------------------------
            # DOCUMENT STATISTICS
            # ---------------------------------------

            st.subheader("📊 Document Statistics")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Pages",
                len(documents)
            )

            col2.metric(
                "Chunks",
                len(chunks)
            )

            col3.metric(
                "Characters",
                len(full_text)
            )

            col4.metric(
                "Words",
                len(full_text.split())
            )

    except Exception as error:
        st.error(
            f"PDF processing error: {error}"
        )

# ---------------------------------------
# AI QUIZ GENERATOR
# ---------------------------------------

st.divider()
st.header("🧠 AI Quiz Generator")

st.write(
    "Generate multiple-choice questions "
    "from your uploaded study material."
)

if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

num_questions = st.selectbox(
    "Number of questions",
    [5, 10],
    key="quiz_num_questions"
)
quiz_topic = st.text_input(
    "Enter Study Topic",
    placeholder="Example: DBMS, Python, Computer Networks",
    key="quiz_topic_input"
)

if st.button("🎯 Generate Quiz"):

    if client is None:
        st.error("Gemini API is not configured.")

    elif not full_text.strip():
        st.warning("Please upload a PDF first.")

    else:
        try:
            with st.spinner("Generating quiz..."):
                questions = generate_quiz(
                    full_text,
                    client,
                    num_questions=num_questions
                )

            st.session_state.quiz_questions = questions
            st.session_state.quiz_submitted = False
            st.session_state.quiz_saved = False
            st.session_state.generated_quiz_topic = (
    quiz_topic.strip() or "General Study"
)

            st.success("Quiz generated successfully!")

        except Exception as error:
            st.error("Unable to generate quiz.")
            st.caption(str(error))


if st.session_state.quiz_questions:

    with st.form("quiz_form"):

        for i, item in enumerate(
            st.session_state.quiz_questions
        ):
            st.subheader(f"Question {i + 1}")
            st.write(item["question"])

            st.radio(
                "Select your answer",
                item["options"],
                key=f"quiz_answer_{i}",
                index=None
            )

        submit_quiz = st.form_submit_button("Submit Quiz")

       
        if submit_quiz:
            score = 0
            questions = st.session_state.quiz_questions

            for i, item in enumerate(questions):
                selected = st.session_state.get(
                    f"quiz_answer_{i}"
                )

                if selected == item["correct_answer"]:
                    score += 1

            # Save quiz score to database
            if not st.session_state.get("quiz_saved", False):
                save_quiz_attempt(
                    topic=st.session_state.get(
                        "generated_quiz_topic",
                        "General Study"
                    ),
                    total_questions=len(questions),
                    score=score
                )
                st.session_state.quiz_saved = True

            st.subheader("📊 Quiz Results")
            st.metric(
                "Your Score",
                f"{score}/{len(questions)}"
            )

            for i, item in enumerate(questions):
                with st.expander(f"Review Question {i + 1}"):
                    st.write(
                        f"Correct Answer: {item['correct_answer']}"
                    )
                    st.write(
                        f"Explanation: {item['explanation']}"
                    )

# ---------------------------------------
# RAG FUNCTION
# ---------------------------------------

def ask_ai(question, vector_database, gemini_client):

    docs = vector_database.similarity_search(
        question,
        k=3
    )

    context = "\n\n".join(
        doc.page_content for doc in docs
    )

    prompt = f"""
You are an AI Study Assistant.

Answer only from the provided PDF context.

If the answer is not available in the context, say:
"I couldn't find the answer in the uploaded PDF."

Give a clear and easy-to-understand answer.

Context:
{context}

Question:
{question}

Answer:
"""

    last_error = None

    for attempt in range(3):
        try:
            response = gemini_client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt
            )

            return response.text, docs

        except Exception as error:
            last_error = error

            if attempt < 2:
                time.sleep(5)

    raise RuntimeError(
        f"Gemini server error: {last_error}"
    )


# ---------------------------------------
# ASK QUESTION
# ---------------------------------------

st.divider()
st.header("💬 Ask Questions")

question = st.text_input(
    "Ask anything from your PDF",
    placeholder="Example: Explain Decision Tree"
)

if st.button(
    "🚀 Ask AI",
    use_container_width=True
):

    if client is None:
        st.error(
        "Gemini API connection failed. "
        "Please verify your API key configuration."
    )

    elif vector_db is None:
        st.error(
            "Please upload and process a PDF first."
        )

    elif not question.strip():
        st.warning(
            "Please enter a question."
        )

    else:
        try:
            with st.spinner(
                "AI is generating the answer..."
            ):
                answer, docs = ask_ai(
                    question,
                    vector_db,
                    client
                )

            st.markdown("## 🤖 AI Answer")
            st.success(answer)

            st.session_state.chat_history.append(
                {
                    "question": question,
                    "answer": answer
                }
            )

            st.subheader("📚 Retrieved Sources")

            for index, doc in enumerate(
                docs,
                start=1
            ):
                with st.expander(
                    f"Source {index}"
                ):
                    st.write(
                        doc.page_content
                    )

        except Exception as error:
            st.error(
                "Gemini server abhi busy hai. "
                "Thodi der baad dobara try karein."
            )

            st.caption(str(error))


# ---------------------------------------
# CHAT HISTORY
# ---------------------------------------

st.divider()
st.header("💬 Chat History")

if st.session_state.chat_history:

    for index, chat in enumerate(
        reversed(
            st.session_state.chat_history
        ),
        start=1
    ):
        with st.expander(
            f"Question {index}: {chat['question']}"
        ):
            st.markdown(
                f"**Question:** {chat['question']}"
            )

            st.markdown(
                f"**Answer:** {chat['answer']}"
            )

    chat_text = ""

    for chat in st.session_state.chat_history:
        chat_text += (
            f"Question: {chat['question']}\n"
        )

        chat_text += (
            f"Answer: {chat['answer']}\n"
        )

        chat_text += (
            "-" * 60 + "\n"
        )

    st.download_button(
        label="📥 Download Chat History",
        data=chat_text,
        file_name="chat_history.txt",
        mime="text/plain",
        use_container_width=True
    )

else:
    st.info(
        "No chat history available."
    )



# ---------------------------------------
# STUDENT PERFORMANCE HISTORY
# ---------------------------------------

st.divider()
st.header("📈 Student Performance History")

history = get_quiz_history()

if history:
    import pandas as pd

    history_df = pd.DataFrame(history)

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    average_accuracy = history_df["accuracy"].mean()

    st.metric(
        "Average Quiz Accuracy",
        f"{average_accuracy:.1f}%"
    )

else:
    st.info(
        "No quiz attempts saved yet. "
        "Complete a quiz to start tracking progress."
    )

# ---------------------------------------
# STUDENT ANALYTICS DASHBOARD
# ---------------------------------------

st.divider()
st.header("📊 Student Analytics Dashboard")

history = get_quiz_history()

if history:
    import pandas as pd
    import plotly.express as px

    df = pd.DataFrame(history)

    # Summary metrics
    total_attempts = len(df)
    average_accuracy = df["accuracy"].mean()
    best_accuracy = df["accuracy"].max()

    col1, col2, col3 = st.columns(3)

    col1.metric("Total Quiz Attempts", total_attempts)
    col2.metric("Average Accuracy", f"{average_accuracy:.1f}%")
    col3.metric("Best Accuracy", f"{best_accuracy:.1f}%")

    # Performance chart
    df = df.sort_values("id")

    fig = px.line(
        df,
        x="id",
        y="accuracy",
        markers=True,
        title="Quiz Accuracy Over Time",
        labels={
            "id": "Quiz Attempt",
            "accuracy": "Accuracy (%)"
        }
    )

    fig.update_yaxes(range=[0, 100])

    st.plotly_chart(fig, use_container_width=True)

    # Recent attempts
    st.subheader("📝 Recent Quiz Attempts")

    st.dataframe(
        df[[
            "quiz_topic",
            "total_questions",
            "score",
            "accuracy",
            "attempted_at"
        ]].sort_values(
            "attempted_at",
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Complete a quiz to view your analytics.") 

# ---------------------------------------
# WEAK TOPIC DETECTION
# ---------------------------------------

st.divider()
st.header("🎯 Weak Topic Detection & Recommendations")

history = get_quiz_history()

if history:
    import pandas as pd

    df = pd.DataFrame(history)

    topic_summary = (
        df.groupby("quiz_topic")
        .agg(
            attempts=("id", "count"),
            average_accuracy=("accuracy", "mean"),
            total_questions=("total_questions", "sum")
        )
        .reset_index()
    )

    topic_summary["average_accuracy"] = (
        topic_summary["average_accuracy"].round(1)
    )

    st.subheader("Topic-wise Performance")

    st.dataframe(
        topic_summary.sort_values("average_accuracy"),
        use_container_width=True,
        hide_index=True
    )

    weak_topics = topic_summary[
        topic_summary["average_accuracy"] < 60
    ].sort_values("average_accuracy")

    if not weak_topics.empty:
        st.subheader("📚 Topics That Need More Practice")

        for _, row in weak_topics.iterrows():
            st.warning(
                f"**{row['quiz_topic']}** — "
                f"Average accuracy: {row['average_accuracy']}%. "
                "Revise this topic and attempt another quiz."
            )
    else:
        st.success(
            "No topic is currently below 60% accuracy. "
            "Continue practising to improve your scores."
        )

else:
    st.info(
        "Complete a quiz to receive topic-wise recommendations."
    )  
# ---------------------------------------
# FOOTER
# ---------------------------------------
    
st.divider()

st.caption(
    "© 2026 AI Powered Study Assistant | "
    "Developed by Ashish Prajapati"
)

# ---------------------------------------
# SMART STUDY PLANNER
# ---------------------------------------

st.divider()
st.header("📅 Smart Study Planner")

st.write(
    "Create a personalized study timetable based on "
    "your exam date, daily study hours, and weak topics."
)

with st.form("study_planner_form"):

    exam_name = st.text_input(
        "Exam / Subject Name",
        placeholder="Example: DBMS End Semester Exam"
    )

    exam_date = st.date_input(
        "Exam Date",
        min_value=__import__("datetime").date.today()
    )

    daily_hours = st.slider(
        "Daily Study Hours",
        min_value=1,
        max_value=12,
        value=3
    )

    weak_topics_input = st.text_area(
        "Weak Topics",
        placeholder="Example: Normalization, SQL Joins, Transactions"
    )

    strong_topics_input = st.text_area(
        "Other Topics to Revise",
        placeholder="Example: ER Model, Keys, SQL Basics"
    )

    create_plan = st.form_submit_button(
        "🚀 Generate Study Plan"
    )

if create_plan:

    if not exam_name.strip():
        st.error("Please enter your exam or subject name.")

    else:
        from datetime import date, timedelta

        today = date.today()
        days_left = (exam_date - today).days

        if days_left < 0:
            st.error("Please select today or a future exam date.")

        else:
            weak_topics = [
                topic.strip()
                for topic in weak_topics_input.split(",")
                if topic.strip()
            ]

            other_topics = [
                topic.strip()
                for topic in strong_topics_input.split(",")
                if topic.strip()
            ]

            all_topics = weak_topics + [
                topic for topic in other_topics
                if topic not in weak_topics
            ]

            st.subheader("📊 Your Study Plan Summary")

            col1, col2, col3 = st.columns(3)

            col1.metric("Days Available", days_left + 1)
            col2.metric("Daily Hours", daily_hours)
            col3.metric(
                "Total Study Hours",
                (days_left + 1) * daily_hours
            )

            if not all_topics:
                all_topics = [exam_name.strip()]

            st.subheader("🗓️ Day-wise Study Timetable")

            schedule = []

            for day_number in range(days_left + 1):

                study_date = today + timedelta(days=day_number)

                if day_number == days_left:
                    tasks = [
                        "Final revision",
                        "Important questions / short notes"
                    ]

                else:
                    topic_index = day_number % len(all_topics)
                    selected_topic = all_topics[topic_index]

                    if selected_topic in weak_topics:
                        tasks = [
                            f"Revise weak topic: {selected_topic}",
                            "Solve practice questions",
                            "Review mistakes"
                        ]
                    else:
                        tasks = [
                            f"Study / revise: {selected_topic}",
                            "Practice questions"
                        ]

                schedule.append({
                    "Date": study_date.strftime("%d-%m-%Y"),
                    "Day": f"Day {day_number + 1}",
                    "Study Tasks": " | ".join(tasks),
                    "Study Hours": daily_hours
                })

            import pandas as pd

            schedule_df = pd.DataFrame(schedule)

            st.dataframe(
                schedule_df,
                use_container_width=True,
                hide_index=True
            )

            st.subheader("💡 Study Recommendations")

            if weak_topics:
                st.info(
                    "Give extra attention to these weak topics: "
                    + ", ".join(weak_topics)
                )
            else:
                st.info(
                    "Add your weak topics next time to personalize "
                    "your revision plan."
                )

            st.success(
                f"Your study plan for {exam_name} is ready!"
            )
            
            saved_plan_id = save_study_plan(
                exam_name=exam_name.strip(),
                exam_date=exam_date,
                daily_hours=daily_hours,
                weak_topics=weak_topics_input.strip(),
                other_topics=strong_topics_input.strip()
            )

            st.success(
                f"Study plan saved successfully! Plan ID: {saved_plan_id}"
            )

            csv_data = schedule_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 Download Study Plan (CSV)",
                data=csv_data,
                file_name="edumind_study_plan.csv",
                mime="text/csv"
            )

# ---------------------------------------
# SAVED STUDY PLAN HISTORY
# ---------------------------------------

st.divider()
st.header("📚 Saved Study Plan History")

saved_plans = get_study_plans()

if saved_plans:
    import pandas as pd

    plans_df = pd.DataFrame(saved_plans)

    plans_df = plans_df.rename(columns={
        "exam_name": "Exam / Subject",
        "exam_date": "Exam Date",
        "daily_hours": "Daily Study Hours",
        "weak_topics": "Weak Topics",
        "other_topics": "Other Topics",
        "created_at": "Plan Created At"
    })

    display_columns = [
        "Exam / Subject",
        "Exam Date",
        "Daily Study Hours",
        "Weak Topics",
        "Other Topics",
        "Plan Created At"
    ]

    st.dataframe(
        plans_df[display_columns],
        use_container_width=True,
        hide_index=True
    )

    st.success(f"Total saved study plans: {len(saved_plans)}")

else:
    st.info(
        "No saved study plans yet. Generate a study plan to see it here."
    )

# ---------------------------------------
# STUDY TASK COMPLETION TRACKER
# ---------------------------------------

st.divider()
st.header("✅ Study Task Completion Tracker")

saved_plans = get_study_plans()

if saved_plans:
    plan_options = {
        f"{plan['exam_name']} - {plan['exam_date']} (ID: {plan['id']})":
        plan["id"]
        for plan in saved_plans
    }

    selected_plan_name = st.selectbox(
        "Select Your Study Plan",
        options=list(plan_options.keys()),
        key="task_tracker_plan"
    )

    selected_plan_id = plan_options[selected_plan_name]

    new_task = st.text_input(
        "Add a Study Task",
        placeholder="Example: Revise DBMS Normalization",
        key="new_study_task"
    )

    if st.button("➕ Add Task"):
        if new_task.strip():
            add_study_task(
                selected_plan_id,
                new_task.strip()
            )
            st.success("Task added successfully!")
            st.rerun()
        else:
            st.warning("Please enter a task name.")

    tasks = get_study_tasks(selected_plan_id)

    if tasks:
        st.subheader("📋 Your Tasks")

        
        for task in tasks:
            st.checkbox(
                task["task_name"],
                value=bool(task["is_completed"]),
                key=f"study_task_{task['id']}",
                on_change=lambda task_id=task["id"]: update_study_task(
                    task_id,
                    st.session_state[f"study_task_{task_id}"]
                )
            )


        completed_count = sum(
            task["is_completed"] for task in tasks
        )

        total_count = len(tasks)
        progress = completed_count / total_count

        st.progress(progress)

        st.metric(
            "Task Completion",
            f"{completed_count}/{total_count}"
        )

        st.caption(
            f"Progress: {progress * 100:.1f}%"
        )

    else:
        st.info(
            "No tasks added yet. Add your first study task above."
        )

else:
    st.info(
        "No saved study plans found. Generate and save a study plan first."
    )

# ---------------------------------------
# STUDENT PROFILE & PERSONALIZED DASHBOARD
# ---------------------------------------

st.divider()
st.header("👨‍🎓 Student Profile")

with st.form("student_profile_form"):
    student_name = st.text_input(
        "Student Name",
        placeholder="Enter your name",
        key="profile_name"
    )

    course = st.selectbox(
        "Course",
        ["B.Tech CSE", "BCA", "MCA", "B.Sc", "Other"],
        key="profile_course"
    )

    semester = st.selectbox(
        "Current Semester",
        ["1", "2", "3", "4", "5", "6", "7", "8"],
        key="profile_semester"
    )

    save_profile = st.form_submit_button(
        "💾 Save Profile"
    )


if save_profile:
    if student_name.strip():
        save_student_profile(
            student_name=student_name.strip(),
            course=course,
            semester=semester
        )

        st.session_state["student_name"] = student_name.strip()
        st.session_state["student_course"] = course
        st.session_state["student_semester"] = semester

        st.success("Student profile saved permanently!")
    else:
        st.warning("Please enter your name.")
saved_profile = get_student_profile()

if saved_profile:
    st.session_state["student_name"] = saved_profile["student_name"]
    st.session_state["student_course"] = saved_profile["course"]
    st.session_state["student_semester"] = saved_profile["semester"]

if st.session_state.get("student_name"):
    st.subheader(
        f"Welcome, {st.session_state['student_name']}! 👋"
    )

    st.write(
        f"**Course:** {st.session_state['student_course']}"
    )
    st.write(
        f"**Semester:** {st.session_state['student_semester']}"
    )

    quiz_history = get_quiz_history()

    st.subheader("📊 Your Learning Overview")

    col1, col2 = st.columns(2)

    col1.metric(
        "Quiz Attempts",
        len(quiz_history)
    )

    if quiz_history:
        import pandas as pd

        history_df = pd.DataFrame(quiz_history)

        if "accuracy" in history_df.columns:
            average_accuracy = history_df["accuracy"].mean()
        else:
            average_accuracy = 0

        col2.metric(
            "Average Accuracy",
            f"{average_accuracy:.1f}%"
        )
    else:
        col2.metric("Average Accuracy", "0%")
