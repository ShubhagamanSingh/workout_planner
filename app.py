import streamlit as st # type: ignore
from huggingface_hub import InferenceClient # type: ignore
from pymongo import MongoClient # type: ignore
import hashlib
from datetime import datetime

# --- Configuration ---
st.set_page_config(
    page_title="Workout & Diet Planner",
    page_icon="💪",
    layout="wide"
)


# --- Custom CSS for Modern UI ---
st.markdown("""
<style>
    .main {
        background-color: black;
    }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 3rem 2rem;
        border-radius: 0 0 25px 25px;
        margin-bottom: 2rem;
        margin-top: -5rem;
        color: white;
        text-align: center;
    }
    
    .custom-card {
        background: white;
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 0.5rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border-left: 5px solid #667eea;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 0.5rem 0;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
    }
    
    .stTextInput input, .stTextArea textarea, .stNumberInput input {
        border-radius: 15px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
        font-size: 1rem;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .success-message {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .info-message {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .plan-section {
        border: 2px solid #e0e0e0;
        border-radius: 15px;
        padding: 1.5rem;
        background: white;
        margin: 1rem 0;
    }
    
    
    
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

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

def display_modern_header():
    """Display modern header with gradient"""
    st.markdown("""
    <div class="header-container">
        <h1 style="margin:0; font-size: 3rem; font-weight: 700;">💪 AI Fitness Coach</h1>
        <p style="margin:0; font-size: 1.3rem; opacity: 0.9; margin-top: 0.5rem;">
        Get personalized workout & diet plans tailored just for you
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_features():
    """Display feature cards"""
    st.markdown("### 🎯 What You'll Get")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h3>🏋️ Personalized Workouts</h3>
            <p>Custom exercises for your goals</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h3>🥗 Smart Meal Plans</h3>
            <p>Delicious & budget-friendly recipes</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h3>📊 Progress Tracking</h3>
            <p>Monitor your fitness journey</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="feature-card">
            <h3>🎯 Goal-Oriented</h3>
            <p>Plans tailored to your objectives</p>
        </div>
        """, unsafe_allow_html=True)

def display_modern_auth():
    """Display modern authentication in sidebar"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 2rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 15px;">
            <h2 style="color: white; margin: 0;">Fitness Coach</h2>
            <p style="color: rgba(255,255,255,0.8); margin: 0;">AI-Powered Plans</p>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state.logged_in:
            tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
            
            with tab1:
                username = st.text_input("Username", key="login_user")
                password = st.text_input("Password", type="password", key="login_pass")
                
                if st.button("Login", use_container_width=True):
                    if username and password:
                        user_data = users_collection.find_one({"_id": username})
                        if user_data and verify_password(user_data["password"], password):
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.rerun()
                        else:
                            st.error("Invalid username or password")
                    else:
                        st.warning("Please enter username and password")
            
            with tab2:
                username = st.text_input("Username", key="reg_user")
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                if st.button("Register", use_container_width=True):
                    if username and password:
                        if password == confirm_password:
                            if users_collection.find_one({"_id": username}):
                                st.error("Username already exists")
                            else:
                                users_collection.insert_one({
                                    "_id": username,
                                    "password": hash_password(password),
                                    "history": []
                                })
                                st.success("Registration successful! Please login.")
                        else:
                            st.error("Passwords do not match")
                    else:
                        st.warning("Please fill all fields")
        else:
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.1); padding: 1.5rem; border-radius: 15px; margin-bottom: 1rem;">
                <h4 style="color: white; margin: 0;">Welcome back!</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0;">{st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()

def display_profile_form():
    """Display modern profile form in sidebar"""
    st.sidebar.markdown("### 📝 Your Profile")
    
    with st.sidebar:
        with st.form(key='profile_form'):
            st.markdown("#### Personal Info")
            age = st.number_input("Age", min_value=16, max_value=80, value=20)
            
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("Weight (kg)", min_value=40.0, max_value=150.0, value=60.0, step=0.5)
            with col2:
                height = st.number_input("Height (cm)", min_value=140.0, max_value=220.0, value=170.0, step=0.5)
            
            gender = st.selectbox("Gender", ["Male", "Female", "Prefer not to say"])

            st.markdown("#### 🎯 Fitness Goals")
            fitness_goal = st.selectbox("Primary Goal", ["Lose Weight", "Gain Muscle", "Improve Fitness & Stamina"])
            workout_days = st.slider("Workout Days per Week", 1, 7, 3)

            st.markdown("#### 💪 Workout Preferences")
            workout_location = st.selectbox("Where do you work out?", ["Home", "Gym"])
            available_equipment = st.text_input("Equipment available", "None", placeholder="dumbbells, yoga mat...")

            st.markdown("#### 🍽️ Dietary Preferences")
            diet_pref = st.selectbox("Diet", ["Anything", "Vegetarian", "Vegan"])
            cuisine_pref = st.text_input("Preferred Cuisine", "Indian", placeholder="Italian, Asian...")
            allergies = st.text_input("Any Allergies?", "None")

            st.markdown("#### 🤔 Additional Details")
            special_info = st.text_area(
                "Injuries, food dislikes, time constraints...",
                placeholder="Tell us anything else we should know..."
            )
            
            submit_button = st.form_submit_button(
                label="🚀 Generate My Plan", 
                use_container_width=True
            )
    
    return (age, weight, height, gender, fitness_goal, workout_days, 
            workout_location, available_equipment, diet_pref, cuisine_pref, 
            allergies, special_info, submit_button)

def display_plan_results(workout_plan, diet_plan):
    """Display the generated plans in a modern layout"""
    st.markdown("""
    <div class="success-message">
        <h3 style="margin:0; color: white;">🎉 Your Personalized Plans Are Ready!</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # Display Plans in Tabs
    plan_tab1, plan_tab2 = st.tabs(["🏋️ Workout Plan", "🥗 Diet Plan"])
    
    with plan_tab1:
        st.markdown("""
        <div class="custom-card">
            <h2 style="color: #333; margin-bottom: 1.5rem;">Your Workout Plan</h2>
        """, unsafe_allow_html=True)
        st.markdown(workout_plan)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with plan_tab2:
        st.markdown("""
        <div class="custom-card">
            <h2 style="color: #333; margin-bottom: 1.5rem;">Your Diet Plan</h2>
        """, unsafe_allow_html=True)
        st.markdown(diet_plan)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Download Button
    full_plan_text = f"""
# Your Personalized Workout & Diet Plan

## 🏋️ Workout Plan
{workout_plan}

---

## 🥗 Diet Plan
{diet_plan}
"""
    st.download_button(
        label="📥 Download Your Full Plan",
        data=full_plan_text,
        file_name=f"fitness_plan_{datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )

def display_modern_history():
    """Display modern history view"""
    st.markdown("""
    <div class="custom-card">
        <h2 style="color: #333; text-align: center; margin-bottom: 2rem;">📚 Your Plan History</h2>
    """, unsafe_allow_html=True)
    
    user_data = users_collection.find_one({"_id": st.session_state.username})
    user_history = user_data.get("history", []) if user_data else []

    if not user_history:
        st.markdown("""
        <div style="text-align: center; padding: 3rem;">
            <h3 style="color: #666;">No plans yet</h3>
            <p>Your fitness plans will appear here!</p>
            <div style="font-size: 4rem;">💪</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for i, entry in enumerate(user_history):
            with st.expander(f"📅 Plan from {entry['date']}", expanded=(i==0)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="plan-section">
                        <h3 style="color: #667eea;">🏋️ Workout Plan</h3>
                    """, unsafe_allow_html=True)
                    st.markdown(entry["workout_plan"])
                    st.markdown("</div>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown("""
                    <div class="plan-section">
                        <h3 style="color: #667eea;">🥗 Diet Plan</h3>
                    """, unsafe_allow_html=True)
                    st.markdown(entry["diet_plan"])
                    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

# --- Main App Interface ---
display_modern_header()

# --- Authentication ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

display_modern_auth()

if not st.session_state.logged_in:
    # Welcome screen for non-logged in users
    st.markdown("""
    <div class="custom-card">
        <h2 style="text-align: center; color: #333; margin-bottom: 2rem;">Welcome to Your AI Fitness Coach! 👋</h2>
        <p style="text-align: center; font-size: 1.2rem; color: #666; line-height: 1.6;">
        Get personalized workout routines and diet plans crafted by AI. 
        Whether you want to lose weight, build muscle, or improve your fitness, 
        we'll create the perfect plan for your lifestyle.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    display_features()
    
    st.markdown("""
    <div class="info-message">
        <p style="margin: 0; font-size: 1.1rem;">
        👈 <strong>Get Started:</strong> Please login or register in the sidebar to begin your fitness journey!
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- Main Application ---
if st.session_state.logged_in:
    # Get form data from sidebar
    form_data = display_profile_form()
    (age, weight, height, gender, fitness_goal, workout_days, 
     workout_location, available_equipment, diet_pref, cuisine_pref, 
     allergies, special_info, submit_button) = form_data

    # --- Main Application Tabs ---
    tab1, tab2 = st.tabs(["🎯 New Plan", "📚 History"])

    with tab1:
        display_features()
        
        if submit_button:
            with st.spinner("🔍 Analyzing your profile..."):
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
            with st.spinner("🏋️ Creating your personalized workout plan..."):
                workout_plan = generate_plan(workout_prompt)
            
            with st.spinner("🥗 Designing your perfect diet plan..."):
                diet_plan = generate_plan(diet_prompt)

            # --- Store plan in history ---
            add_plan_to_history(st.session_state.username, workout_plan, diet_plan)

            # Display results
            display_plan_results(workout_plan, diet_plan)
        else:
            st.markdown("""
            <div class="custom-card">
                <h2 style="text-align: center; color: #333; margin-bottom: 1rem;">Ready to Transform Your Fitness? 🚀</h2>
                <p style="text-align: center; color: #666; font-size: 1.1rem;">
                Fill out your profile in the sidebar and click <strong>"Generate My Plan"</strong> to get started!
                </p>
                <div style="text-align: center; font-size: 4rem; margin: 2rem 0;">💪</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        display_modern_history()
