import os
import json
import streamlit as st
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# 1. INITIALIZATION & SETUP
# ---------------------------------------------------------------------------
st.set_page_config(page_title="AI Study Buddy", page_icon="📚", layout="wide")

# Retrieve API key from environment variable or sidebar input
api_key = os.environ.get("GEMINI_API_KEY", "")

with st.sidebar:
    st.header("🔑 Configuration")
    if not api_key:
        api_key = st.text_input("Enter your Gemini API Key:", type="password")
    else:
        st.success("API Key detected from environment!")
    
    st.markdown("---")
    st.markdown("### How to use:")
    st.markdown("1. Choose a feature from the top tabs.\n"
                "2. Input your topic or notes.\n"
                "3. Let the AI help you study!")

# Initialize the Gemini Client if key is available
if api_key:
    client = genai.Client(api_key=api_key)
else:
    st.warning("Please provide a Gemini API Key in the sidebar to start.")
    st.stop()

# Using the standard flash model for fast, cost-effective processing
MODEL_ID = 'gemini-2.5-flash'

# ---------------------------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------------------------
def generate_ai_response(prompt: str) -> str:
    """Handles standard text generation requests."""
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"Error generating content: {str(e)}"

def generate_quiz_data(topic: str, num_questions: int = 3) -> list:
    """Generates structured JSON data for quizzes using Structured Outputs."""
    prompt = f"Generate a {num_questions}-question multiple-choice quiz about: {topic}."
    
    # Define the schema using Pydantic-like structure via types.Schema
    quiz_schema = types.Schema(
        type=types.Type.ARRAY,
        items=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "question": types.Schema(type=types.Type.STRING),
                "options": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING)
                ),
                "correct_answer": types.Schema(type=types.Type.STRING),
                "explanation": types.Schema(type=types.Type.STRING)
            },
            required=["question", "options", "correct_answer", "explanation"]
        )
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=quiz_schema,
                temperature=0.2 # Lower temperature for factual accuracy
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Failed to generate quiz: {e}")
        return []

# ---------------------------------------------------------------------------
# 3. USER INTERFACE & TABS
# ---------------------------------------------------------------------------
st.title("📚 AI-Powered Study Buddy")
st.caption("Your personalized AI tutor for simplifying concepts, summarizing notes, and testing your knowledge.")

# Create tabs for different functionalities
tab1, tab2, tab3, tab4 = st.tabs([
    "🧠 Explain Like I'm 5", 
    "📝 Notes Summarizer", 
    "📇 Flashcard Generator", 
    "✏️ Practice Quiz"
])

# --- TAB 1: EXPLAIN LIKE I'M 5 ---
with tab1:
    st.header("Simplify Complex Concepts")
    concept = st.text_input("What complex topic or concept are you trying to understand?", 
                            placeholder="e.g., Quantum Entanglement, Photosynthesis, Inflation")
    
    if st.button("Explain It Simply", type="primary"):
        if concept:
            with st.spinner("Breaking it down into simple terms..."):
                prompt = (f"Explain the concept of '{concept}' in incredibly simple terms. "
                          f"Use analogies that a 10-year-old would understand, avoid heavy jargon, "
                          f"and format it with clear headings and bullet points.")
                explanation = generate_ai_response(prompt)
                st.markdown("### 💡 Explanation:")
                st.markdown(explanation)
        else:
            st.warning("Please enter a concept first.")

# --- TAB 2: NOTES SUMMARIZER ---
with tab2:
    st.header("Streamline Your Notes")
    raw_notes = st.text_area("Paste your messy or long study notes below:", height=250,
                             placeholder="Paste textbook chapters, lecture transcripts, or messy notes here...")
    
    if st.button("Summarize Notes", type="primary"):
        if raw_notes:
            with st.spinner("Extracting key takeaways..."):
                prompt = (f"Analyze the following study notes. Provide a concise summary containing:\n"
                          f"1. A high-level TL;DR overview.\n"
                          f"2. Key definitions or formulas.\n"
                          f"3. Core takeaways in bullet points.\n\n"
                          f"Notes:\n{raw_notes}")
                summary = generate_ai_response(prompt)
                st.markdown("### 📌 Study Summary:")
                st.markdown(summary)
        else:
            st.warning("Please paste some notes to summarize.")

# --- TAB 3: FLASHCARD GENERATOR ---
with tab3:
    st.header("Quick-Study Flashcards")
    flashcard_topic = st.text_input("Enter a topic or paste text to build flashcards from:", 
                                    placeholder="e.g., French Revolution Timeline, Mitosis Stages")
    
    if st.button("Generate Flashcards", type="primary"):
        if flashcard_topic:
            with st.spinner("Creating flashcards..."):
                prompt = (f"Create 5 high-yield study flashcards based on: {flashcard_topic}. "
                          f"Format them clearly as:\n"
                          f"**Card X FRONT:** [Question/Term]\n"
                          f"**Card X BACK:** [Answer/Definition]\n"
                          f"Separate each card with a horizontal line (---).")
                cards = generate_ai_response(prompt)
                
                st.markdown("### 📇 Your Flashcards")
                # Split by horizontal lines to make them look distinct in UI
                card_list = cards.split("---")
                for card in card_list:
                    if card.strip():
                        st.info(card.strip())
        else:
            st.warning("Please provide a topic or text.")

# --- TAB 4: PRACTICE QUIZ ---
with tab4:
    st.header("Test Your Knowledge")
    quiz_topic = st.text_input("What topic would you like to be tested on?", 
                               placeholder="e.g., Basic Python Loops, Human Anatomy, WW2 History")
    
    # Track quiz state so inputs don't reset on every button click/re-render
    if "current_quiz" not in st.session_state:
        st.session_state.current_quiz = None
    if "quiz_topic_tracked" not in st.session_state:
        st.session_state.quiz_topic_tracked = ""

    # If the user changes the topic text, clear the previous quiz
    if quiz_topic != st.session_state.quiz_topic_tracked:
        st.session_state.current_quiz = None

    if st.button("Generate 3-Question Quiz", type="primary"):
        if quiz_topic:
            with st.spinner("Generating quiz questions..."):
                st.session_state.current_quiz = generate_quiz_data(quiz_topic, num_questions=3)
                st.session_state.quiz_topic_tracked = quiz_topic
        else:
            st.warning("Please enter a topic for the quiz.")

    # Render the quiz if it exists in session state
    if st.session_state.current_quiz:
        st.markdown("---")
        st.markdown(f"### ✏️ Quiz: {st.session_state.quiz_topic_tracked}")
        
        # We wrap the quiz submission form so it evaluates answers together
        with st.form("quiz_form"):
            user_answers = {}
            for idx, q in enumerate(st.session_state.current_quiz):
                st.markdown(f"**Q{idx+1}: {q['question']}**")
                # Radio button for multiple choice options
                user_answers[idx] = st.radio(
                    f"Select your answer for Q{idx+1}:", 
                    options=q['options'], 
                    key=f"q_opt_{idx}"
                )
                st.markdown("")
                
            submitted = st.form_submit_with_button("Submit Answers")
            
            if submitted:
                score = 0
                st.markdown("### 📊 Results:")
                for idx, q in enumerate(st.session_state.current_quiz):
                    u_ans = user_answers[idx]
                    c_ans = q['correct_answer']
                    
                    if u_ans == c_ans:
                        score += 1
                        st.success(f"**Question {idx+1}: Correct!** ✅")
                    else:
                        st.error(f"**Question {idx+1}: Incorrect.** ❌\n* Your answer: {u_ans}\n* Correct answer: {c_ans}")
                    
                    st.caption(f"ℹ️ *Explanation:* {q['explanation']}\n")
                
                st.metric(label="Final Score", value=f"{score} / {len(st.session_state.current_quiz)}")
                
                # C:\Users\DELL\OneDrive\Desktop\Poetry\Intern Project\AI-Powered_Study_buddy.py