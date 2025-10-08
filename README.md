# AI Personalized Workout & Diet Planner

This Streamlit application provides personalized workout and diet plans for students using AI. It considers individual needs, fitness goals, dietary preferences, and available resources to generate practical, budget-friendly, and effective routines.

## ✨ Features

- **User-Friendly Interface**: A clean sidebar for input and tabbed layout for results.
- **Deep Personalization**: Collects details on age, weight, height, fitness goals, workout location, available equipment, and dietary preferences.
- **AI-Powered**: Uses a powerful language model from Hugging Face to generate custom plans.
- **Student-Focused**: Prompts are designed to create plans that are practical and budget-friendly for students.
- **Secure**: Uses Streamlit's secrets management to keep your API token safe.

## 🚀 Setup and Installation Guide

Follow these steps to get the application running on your local machine.

### Step 1: Get Your Hugging Face API Token

The application uses a model from the Hugging Face Hub, which requires an API token.

1.  Go to the Huggind Face website and create an account or log in: [huggingface.co](https://huggingface.co/)
2.  Navigate to your profile settings by clicking on your profile picture in the top-right corner.
3.  Go to **Settings** -> **Access Tokens**.
4.  Click on **"New token"**. Give it a name (e.g., "Streamlit App") and assign it a `read` role.
5.  Click **"Generate a token"** and copy the generated token (`hf_...`). **You will not be able to see it again, so copy it now!**

### Step 2: Create the Secrets File

Streamlit uses a `.streamlit/secrets.toml` file to store sensitive information like API keys.

1.  In your project's root directory (`workout_planner/`), create a new folder named `.streamlit`.
2.  Inside the `.streamlit` folder, create a new file named `secrets.toml`.
3.  Add your Hugging Face token to this file as shown below:

    ```toml
    # .streamlit/secrets.toml
    HF_TOKEN = "hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    ```
    *Replace `hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` with the actual token you copied.*

### Step 3: Install Dependencies

Open your terminal or command prompt, navigate to the project's root directory (`workout_planner/`), and run the following command to install the required Python packages:

```bash
pip install -r requirements.txt
```

### Step 4: Run the Streamlit App

Once the installation is complete, run the following command in your terminal:

```bash
streamlit run app.py
```

Your web browser should automatically open with the application running!

## 📁 Project Structure
workout_planner/
├── .streamlit/
│   └── secrets.toml         # Contains Streamlit app secrets (API keys, config, etc.)
├── app.py                   # Main Streamlit application file
├── requirements.txt         # List of dependencies and libraries required for the project
└── README.md                # Project documentation file

