import streamlit as st # type: ignore
from huggingface_hub import InferenceClient # type: ignore
from pymongo import MongoClient # type: ignore
import hashlib
from datetime import datetime
# --- Configuration ---
st.set_page_config(
    page_title="Workout & Diet Planner",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed on mobile
)
# --- Custom CSS for Mobile-Friendly UI ---
st.markdown("""
<style>
    .main {
        background-color: black;
    }
    
    .header-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 1rem;
        border-radius: 0 0 25px 25px;
        margin-bottom: 2rem;
        margin-top: -10rem;
        color: white;
        text-align: center;
    }
    
    .custom-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .feature-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.3rem;
    }
    
    .mobile-sidebar-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
        margin: 0.5rem 0;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    
    /* Mobile-specific styles */
    @media (max-width: 768px) {
        .header-container {
            padding: 1.5rem 1rem;
        }
        
        .header-container h1 {
            font-size: 2rem !important;
        }
        
        .custom-card {
            padding: 1rem;
            margin-bottom: 0.8rem;
        }
        
        .feature-card {
            padding: 0.8rem;
            margin: 0.2rem;
        }
        
        /* Make sidebar more accessible on mobile */
        .css-1d391kg {
            width: 85% !important;
        }
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)



# [Keep all your existing backend functions and MongoDB code exactly the same...]
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
    pass

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hash_password(provided_password)

def add_plan_to_history(username, workout_plan, diet_plan):
    plan_entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "workout_plan": workout_plan,
        "diet_plan": diet_plan
    }
    users_collection.update_one(
        {"_id": username},
        {"$push": {"history": {"$each": [plan_entry], "$position": 0}}}
    )

# Hugging Face token
try:
    HF_TOKEN = st.secrets["HF_TOKEN"]
except FileNotFoundError:
    st.error("Streamlit secrets file not found. Please create a .streamlit/secrets.toml file with your HF_TOKEN.")
    st.stop()

client = InferenceClient("meta-llama/Meta-Llama-3-8B-Instruct", token=HF_TOKEN)

def generate_plan(prompt):
    messages = [
        {
            "role": "system",
            "content": "You are an expert fitness and nutrition coach for students. Your goal is to create practical, budget-friendly, and effective workout and diet plans. Be encouraging and clear in your instructions. Format your response using Markdown.",
        },
        {"role": "user", "content": prompt},
    ]

    response_text = ""
    try:
        for chunk in client.chat_completion(messages, max_tokens=1024, temperature=0.8, stream=True):
            if chunk.choices and chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
    except Exception as e:
        st.error(f"An error occurred while communicating with the AI model: {e}")
        return "Sorry, I couldn't generate a plan at this moment. Please try again later."
        
    return response_text.strip()

# --- Mobile-Friendly UI Components ---
def display_mobile_sidebar_button():
    """Display a prominent button to open sidebar on mobile"""
    st.markdown("""
    <div style="text-align: center; margin: 1rem 0;">
        <button class="mobile-sidebar-button" onclick="document.querySelector('[data-testid=\"stSidebar\"]').style.width = '85%'">
            📝 Open Settings & Profile
        </button>
    </div>
    """, unsafe_allow_html=True)

def display_mobile_instructions():
    """Show mobile-specific instructions"""
    st.markdown("""
    <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 1rem 0; border-left: 4px solid #2196F3;">
        <h4 style="margin:0 0 0.5rem 0; color: #1976d2;">📱 Mobile Tips</h4>
        <p style="margin:0; color: #555;">
        <strong>To access settings:</strong> Swipe from right edge or tap ☰ menu<br>
        <strong>Need help?</strong> Use the button above to open sidebar
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_modern_header():
    st.markdown("""
    <div class="header-container">
        <h1 style="margin:0; font-size: 2.5rem; font-weight: 700;">💪 AI Fitness Coach</h1>
        <p style="margin:0; font-size: 1.1rem; opacity: 0.9; margin-top: 0.5rem;">
        Get personalized workout & diet plans
        </p>
    </div>
    """, unsafe_allow_html=True)

def display_features():
    st.markdown("### 🎯 What You'll Get")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>🏋️ Personalized Workouts</h4>
            <p>Custom exercises for your goals</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Progress Tracking</h4>
            <p>Monitor your fitness journey</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>🥗 Smart Meal Plans</h4>
            <p>Delicious & budget-friendly</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="feature-card">
            <h4>🎯 Goal-Oriented</h4>
            <p>Tailored to your objectives</p>
        </div>
        """, unsafe_allow_html=True)

# --- Updated Authentication with Mobile Support ---
def display_modern_auth():
    """Display authentication in sidebar with mobile considerations"""
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 1rem; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 15px;">
            <h3 style="color: white; margin: 0;">Fitness Coach</h3>
            <p style="color: rgba(255,255,255,0.8); margin: 0;">AI-Powered Plans</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mobile close button (visible only on mobile)
        st.markdown("""
        <div style="text-align: right; margin-bottom: 1rem;">
            <button style="background: rgba(255,255,255,0.2); color: white; border: none; border-radius: 50%; width: 30px; height: 30px; font-size: 1.2rem;" 
                    onclick="document.querySelector('[data-testid=\"stSidebar\"]').style.width = '0'">×</button>
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
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 15px; margin-bottom: 1rem;">
                <h4 style="color: white; margin: 0;">Welcome!</h4>
                <p style="color: rgba(255,255,255,0.8); margin: 0.5rem 0;">{st.session_state.username}</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.username = ""
                st.rerun()

# --- Updated Main App Interface ---
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
        <h2 style="text-align: center; color: #333; margin-bottom: 1rem;">Welcome to AI Fitness Coach! 👋</h2>
        <p style="text-align: center; color: #666;">
        Get personalized workout routines and diet plans crafted by AI.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mobile-friendly access instructions
    display_mobile_sidebar_button()
    display_mobile_instructions()
    
    display_features()

# --- Main Application ---
if st.session_state.logged_in:
    # Mobile sidebar access button
    display_mobile_sidebar_button()
    
    # Profile form in sidebar
    with st.sidebar:
        if st.session_state.logged_in:
            st.markdown("### 📝 Your Profile")
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
                available_equipment = st.text_input("Equipment available", "None")

                st.markdown("#### 🍽️ Dietary Preferences")
                diet_pref = st.selectbox("Diet", ["Anything", "Vegetarian", "Vegan"])
                cuisine_pref = st.text_input("Preferred Cuisine", "Indian")
                allergies = st.text_input("Any Allergies?", "None")

                st.markdown("#### 🤔 Additional Details")
                special_info = st.text_area("Injuries, food dislikes, time constraints...")
                
                submit_button = st.form_submit_button(
                    label="🚀 Generate My Plan", 
                    use_container_width=True
                )

    # Main content area
    tab1, tab2 = st.tabs(["🎯 New Plan", "📚 History"])

    with tab1:
        display_features()
        
        if 'submit_button' in locals() and submit_button:
            with st.spinner("🔍 Analyzing your profile..."):
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

            with st.spinner("🏋️ Creating your personalized workout plan..."):
                workout_plan = generate_plan(workout_prompt)
            
            with st.spinner("🥗 Designing your perfect diet plan..."):
                diet_plan = generate_plan(diet_prompt)

            add_plan_to_history(st.session_state.username, workout_plan, diet_plan)

            # Display results
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); color: white; padding: 1.5rem; border-radius: 15px; text-align: center; margin: 1rem 0;">
                <h3 style="margin:0; color: white;">🎉 Your Personalized Plans Are Ready!</h3>
            </div>
            """, unsafe_allow_html=True)
            
            plan_tab1, plan_tab2 = st.tabs(["🏋️ Workout Plan", "🥗 Diet Plan"])
            
            with plan_tab1:
                st.markdown("""
                <div class="custom-card">
                    <h3 style="color: #333; margin-bottom: 1rem;">Your Workout Plan</h3>
                """, unsafe_allow_html=True)
                st.markdown(workout_plan)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with plan_tab2:
                st.markdown("""
                <div class="custom-card">
                    <h3 style="color: #333; margin-bottom: 1rem;">Your Diet Plan</h3>
                """, unsafe_allow_html=True)
                st.markdown(diet_plan)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="custom-card">
                <h3 style="text-align: center; color: #333; margin-bottom: 1rem;">Ready to Transform Your Fitness? 🚀</h3>
                <p style="text-align: center; color: #666;">
                Open the sidebar to fill out your profile and click <strong>"Generate My Plan"</strong>!
                </p>
                <div style="text-align: center; font-size: 3rem; margin: 1rem 0;">💪</div>
            </div>
            """, unsafe_allow_html=True)

    with tab2:
        st.markdown("""
        <div class="custom-card">
            <h2 style="color: #333; text-align: center; margin-bottom: 1rem;">📚 Your Plan History</h2>
        """, unsafe_allow_html=True)
        
        user_data = users_collection.find_one({"_id": st.session_state.username})
        user_history = user_data.get("history", []) if user_data else []

        if not user_history:
            st.markdown("""
            <div style="text-align: center; padding: 2rem;">
                <h4 style="color: #666;">No plans yet</h4>
                <p>Your fitness plans will appear here!</p>
                <div style="font-size: 3rem;">💪</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for i, entry in enumerate(user_history):
                with st.expander(f"📅 Plan from {entry['date']}", expanded=(i==0)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**🏋️ Workout Plan**")
                        st.markdown(entry["workout_plan"])
                    
                    with col2:
                        st.markdown("**🥗 Diet Plan**")
                        st.markdown(entry["diet_plan"])
        
        st.markdown("</div>", unsafe_allow_html=True)



