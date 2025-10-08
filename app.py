import streamlit as st # type: ignore
from huggingface_hub import InferenceClient # type: ignore
from pymongo import MongoClient # type: ignore
import json
import hashlib
from datetime import datetime
import os

# --- Configuration ---
st.set_page_config(
    page_title="AI Workout & Diet Planner",
    page_icon="💪",
    layout="wide"
)

# --- User Authentication and Data Management ---
# --- MongoDB Connection ---
@st.cache_resource
def get_mongo_client():
    """Establishes a connection to MongoDB and returns the collection object."""
    try:
        MONGO_URI = st.secrets["MONGO_URI"]
        DB_NAME = st.secrets["DB_NAME"]
        COLLECTION_NAME = st.secrets["COLLECTION_NAME"]
        client = MongoClient(MONGO_URI)
        return client[DB_NAME][COLLECTION_NAME]
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        st.stop()

users_collection = get_mongo_client()

def load_users():
    """Loads a specific user from MongoDB."""
    # This function is no longer needed in this form, we'll query directly.
    # We keep it as a placeholder to minimize code changes, but it's unused.
    pass

def hash_password(password):
    """Hashes a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verifies a provided password against a stored hash."""
    return stored_password == hash_password(provided_password)

def add_plan_to_history(username, workout_plan, diet_plan):
    """Adds a generated plan to the user's history."""
    plan_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workout_plan": workout_plan,
        "diet_plan": diet_plan
    }
    users_collection.update_one(
        {"_id": username},
        {"$push": {"history": {"$each": [plan_entry], "$position": 0}}}
    )

# Hugging Face token (securely stored in Streamlit secrets)
# Make sure to add HF_TOKEN to your Streamlit secrets
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except FileNotFoundError:
    st.error("Streamlit secrets file not found. Please create a .streamlit/secrets.toml file with your HF_TOKEN.")
    st.stop()

client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

# --- Helper Function to Generate Plans ---
def generate_plan(prompt):
    """
    Generates a response from the LLaMA model based on a detailed prompt.
    """
    messages = [
        {
            "role": "system",
            "content": "You are an expert fitness and nutrition coach for students. Your goal is to create practical, budget-friendly, and effective workout and diet plans. Be encouraging and clear in your instructions. Format your response using Markdown.",
        },
        {"role": "user", "content": prompt},
    ]

    response_text = ""
    try:
        # Use chat_completion for conversational models like Llama-3
        for chunk in client.chat_completion(messages, max_tokens=1024, temperature=0.8, stream=True):
            # Add a check to ensure the choices list is not empty before accessing it
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"An error occurred while communicating with the AI model: {e}")
        return "Sorry, I couldn't generate a plan at this moment. Please try again later."
        
    return response_text.strip()

# --- Main App Interface ---
st.title("💪 Workout & Diet Planner")

# --- Authentication UI ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.sidebar.title("Login / Register")
    choice = st.sidebar.radio("Choose an action", ["Login", "Register"])

    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if choice == "Register":
        if st.sidebar.button("Register"):
            if username and password:
                # Check if user already exists
                if users_collection.find_one({"_id": username}):
                    st.sidebar.error("Username already exists.")
                else:
                    users_collection.insert_one({
                        "_id": username,
                        "password": hash_password(password),
                        "history": []
                    })
                    st.sidebar.success("Registration successful! Please log in.")
            else:
                st.sidebar.warning("Please enter a username and password.")

    if choice == "Login":
        if st.sidebar.button("Login"):
            if username and password:
                user_data = users_collection.find_one({"_id": username})
                if user_data and verify_password(user_data["password"], password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun() # Rerun the script to show the main app
                else:
                    st.sidebar.error("Invalid username or password.")
            else:
                st.sidebar.warning("Please enter your username and password.")

    st.info("Please log in or register to use the planner.")

# --- Main Application ---
if st.session_state.logged_in:
    st.sidebar.title(f"Welcome, {st.session_state.username}! 👋")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    # --- UI: Sidebar for User Input ---
    st.sidebar.header("Tell Me About Yourself 📝")
    with st.sidebar:
        with st.form(key='profile_form'):
            st.subheader("Personal Info")
            age = st.number_input("Age", min_value=16, max_value=80, value=20)
            weight = st.number_input("Weight (kg)", min_value=40.0, max_value=150.0, value=60.0, step=0.5)
            height = st.number_input("Height (cm)", min_value=140.0, max_value=220.0, value=170.0, step=0.5)
            gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])

            st.subheader("Fitness Goals")
            fitness_goal = st.selectbox("Primary Goal", ["Lose Weight", "Gain Muscle", "Improve Fitness & Stamina"])
            workout_days = st.slider("Workout Days per Week", 1, 7, 3)

            st.subheader("Workout Preferences")
            workout_location = st.selectbox("Where do you work out?", ["Home", "Gym"])
            available_equipment = st.text_input("Equipment available (e.g., dumbbells, yoga mat)", "None")

            st.subheader("Dietary Preferences")
            diet_pref = st.selectbox("Diet", ["Anything", "Vegetarian", "Vegan"])
            cuisine_pref = st.text_input("Preferred Cuisine (e.g., Indian, Italian)", "Indian")
            allergies = st.text_input("Any Allergies?", "None")

            st.subheader("Anything Else? 🤔")
            special_info = st.text_area(
                "Add any other details (e.g., injuries, specific food dislikes, time constraints)",
                ""
            )
            submit_button = st.form_submit_button(label="✨ Generate My Plan", use_container_width=True)

    # --- Main Content Area ---
    main_tab1, main_tab2 = st.tabs(["🌟 New Plan", "📜 History"])

    with main_tab1:
        if submit_button:
            with st.spinner("Checking your details..."):
                # --- Prompt Engineering ---
                special_notes_prompt_section = ""
                if special_info and special_info.strip():
                    special_notes_prompt_section = f"\nImportant Additional Notes from the user: {special_info}"

                workout_prompt = f"""
                Create a personalized workout plan for a {age}-year-old {gender} student who is {height} cm tall and weighs {weight} kg.
                Primary Goal: {fitness_goal}.
                Workout Schedule: {workout_days} days a week.
                Workout Location: {workout_location}.
                Available Equipment: {available_equipment}.
                {special_notes_prompt_section}
                Please provide a weekly schedule. For each workout day, list the exercises with sets and reps. Include a warm-up and cool-down routine. Make the plan encouraging and easy to follow for a student.
                """

                diet_prompt = f"""
                Create a personalized, budget-friendly, 1-day sample meal plan for a {age}-year-old {gender} student with the goal of '{fitness_goal}'.
                Dietary Preference: {diet_pref}.
                Preferred Cuisine: {cuisine_pref}.
                Allergies: {allergies}.
                {special_notes_prompt_section}
                The plan should be simple, using easily available ingredients suitable for a student's budget. Provide options for Breakfast, Lunch, Dinner, and one Snack. Make it sound delicious and motivating!
                """

            # --- Plan Generation ---
            with st.spinner("Crafting your personalized plans... This may take a moment. 🧘"):
                workout_plan = generate_plan(workout_prompt)
                diet_plan = generate_plan(diet_prompt)

            st.success("Your personalized plans are ready! 🎉")

            # --- Store plan in history ---
            add_plan_to_history(st.session_state.username, workout_plan, diet_plan)

            # --- Display Plans in Tabs ---
            plan_tab1, plan_tab2 = st.tabs(["🏋️ Workout Plan", "🥗 Diet Plan"])

            with plan_tab1:
                st.header("Your Personalized Workout Plan")
                st.markdown(workout_plan)

            with plan_tab2:
                st.header("Your Personalized Diet Plan")
                st.markdown(diet_plan)

            # --- Add Download Button ---
            full_plan_text = f"""
# Your Personalized Workout & Diet Plan

## 🏋️ Workout Plan
{workout_plan}

---

## 🥗 Diet Plan
{diet_plan}
"""
            st.download_button(
                label="📥 Download Your Full Plan (.txt)",
                data=full_plan_text,
                file_name=f"plan_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain"
            )
        else:
            st.info("Fill in your details in the sidebar and click 'Generate My Plan' to start!")

    with main_tab2:
        st.header("Your Plan History")
        user_data = users_collection.find_one({"_id": st.session_state.username})
        user_history = user_data.get("history", []) if user_data else []

        if not user_history:
            st.info("You have no saved plans yet. Generate a new plan to see it here!")
        else:
            for i, entry in enumerate(user_history):
                with st.expander(f"Plan from {entry['date']}"):
                    st.subheader("🏋️ Workout Plan")
                    st.markdown(entry["workout_plan"])
                    st.subheader("🥗 Diet Plan")
                    st.markdown(entry["diet_plan"])
