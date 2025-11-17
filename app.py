import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

# --- 1. DATA STRUCTURES ---

class UserProfile:
    """
    Holds the static, long-term data for a single user.
    This data personalizes the AI model.
    """
    def __init__(self, name, age, diagnosis_type, years_since_diagnosis, bmi, on_metformin, on_insulin):
        # Demographics
        self.name = name
        self.age = int(age)
        
        # Clinical Profile
        self.diagnosis_type = diagnosis_type # e.g., "Prediabetes" or "Type 2"
        self.years_since_diagnosis = int(years_since_diagnosis)
        self.bmi = float(bmi)
        
        # Medications
        self.on_metformin = bool(on_metformin)
        self.on_insulin = bool(on_insulin)
        
        # This will hold all the user's daily logs
        self.logs = [] 

    def __repr__(self):
        # A simple way to print the user's info
        return f"<UserProfile: {self.name}, {self.age}, {self.diagnosis_type}>"

class DailyLog:
    """
    Holds the dynamic, daily inputs from the user.
    This is the data our AI will use for real-time predictions.
    """
    def __init__(self, date, sleep_hours, sleep_quality, carbs_g, protein_g, fat_g, activity_minutes, took_metformin, took_insulin):
        self.date = date
        
        # Logged Data
        self.sleep_hours = float(sleep_hours)
        self.sleep_quality = sleep_quality # e.g., "poor", "good", "excellent"
        self.carbs_g = int(carbs_g)
        self.protein_g = int(protein_g)
        self.fat_g = int(fat_g)
        self.activity_minutes = int(activity_minutes)
        
        # Medication Adherence
        self.took_metformin = bool(took_metformin)
        self.took_insulin = bool(took_insulin)

    def __repr__(self):
        # A simple way to print the log's info
        return f"<DailyLog: {self.date.strftime('%Y-%m-%d')}, Carbs: {self.carbs_g}g>"

# --- 2. AI PREDICTION ENGINE (The "Brain") ---

def get_prediction_and_explanation(user: UserProfile, log: DailyLog):
    """
    Simulates a trained ML model (like a Random Forest)
    by analyzing the user's profile and latest log.
    
    Returns:
        - risk_score (float): A score from 0.0 (low risk) to 1.0 (high risk).
        - explanation (dict): A dictionary explaining what factors contributed to the score.
    """
    risk_score = 0.0
    explanation = {}
    
    # --- 1. Analyze Dietary Factors ---
    if log.carbs_g > 80:
        carb_risk = 0.40 
        risk_score += carb_risk
        explanation["High-Carb Meal ( > 80g)"] = carb_risk
    
    # --- 2. Analyze Lifestyle Factors ---
    if log.sleep_hours < 6:
        sleep_risk = 0.15
        risk_score += sleep_risk
        explanation["Poor Sleep ( < 6 hours)"] = sleep_risk
        
    if log.activity_minutes < 10:
        activity_risk = 0.15
        risk_score += activity_risk
        explanation["Low Activity ( < 10 min)"] = activity_risk

    # --- 3. Analyze Personalized Clinical Factors ---
    if user.on_metformin and not log.took_metformin:
        metformin_risk = 0.30 # Missing meds is a high-impact event
        risk_score += metformin_risk
        explanation["Missed Metformin Dose"] = metformin_risk
        
    if user.on_insulin and not log.took_insulin:
        insulin_risk = 0.50 # Missing insulin is critical
        risk_score += insulin_risk
        explanation["Missed Insulin Dose"] = insulin_risk
        
    # --- 4. Analyze Compounding Factors (Personalization) ---
    if user.bmi > 28 and risk_score > 0:
        bmi_amplifier = 0.10
        risk_score += bmi_amplifier
        explanation["Risk amplified by BMI"] = bmi_amplifier
        
    if user.years_since_diagnosis > 5 and risk_score > 0:
        duration_amplifier = 0.10
        risk_score += duration_amplifier
        explanation["Risk amplified by T2D duration"] = duration_amplifier

    # --- 5. Finalize the Score ---
    final_risk_score = min(risk_score, 1.0)
    
    return final_risk_score, explanation

# --- 3. PERSONALIZED FEEDBACK ENGINE (The "Voice") ---

def generate_personalized_feedback(user: UserProfile, log: DailyLog, risk_score: float, explanation: dict):
    """
    Analyzes the risk and explanation to generate a
    helpful, actionable suggestion for the user.
    """
    
    # Check for the most critical factors first
    if "Missed Insulin Dose" in explanation:
        return ("CRITICAL: You logged that you missed your insulin. "
                "Please follow your doctor's advice on what to do "
                "when you miss a dose. This is the #1 reason for your high-risk score.")

    if "Missed Metformin Dose" in explanation:
        return ("HIGH PRIORITY: We noticed you may have missed your Metformin. "
                "This is a key factor in your risk today. "
                "Try to set a reminder for your next dose.")

    # If no critical events, check for high-risk combinations
    if risk_score > 0.7:
        if "High-Carb Meal ( > 80g)" in explanation and "Low Activity ( < 10 min)" in explanation:
            return ("This is a high-risk combination. You've logged a high-carb meal "
                    "and low activity. "
                    "**Actionable Suggestion:** Can you take a 15-20 minute walk in the next hour? "
                    "This is the best way to help your body manage the carbs.")
        
        if "High-Carb Meal ( > 80g)" in explanation and "Poor Sleep ( < 6 hours)" in explanation:
            return ("Your risk is high. Poor sleep can make you more insulin resistant, "
                    "and the high-carb meal adds to that. "
                    "**Actionable Suggestion:** Be mindful of your next meal, "
                    "and let's focus on getting more rest tonight.")

    # Check for moderate-risk factors
    elif risk_score > 0.4:
        if "High-Carb Meal ( > 80g)" in explanation:
            return ("MODERATE RISK: Your meal was high in carbs. "
                    "**Actionable Suggestion:** A quick 10-minute walk would be a "
                    "great way to help balance it out.")
        
        if "Poor Sleep ( < 6 hours)" in explanation:
            return ("MODERATE RISK: You logged poor sleep. This can affect your "
                    "sugar levels all day. Your body may be more sensitive to carbs today, "
                    "so let's try to plan for a good night's rest tonight.")

    # If risk is low, provide positive reinforcement
    else:
        return ("✅ GREAT JOB! Your risk score is low. "
                "Your logs show you're balancing your meals, activity, and medication well. "
                "Keep up the fantastic work!")

    # A default catch-all
    return "Please be mindful of your logged items, as they are contributing to a higher risk."


# --- 4. FLASK API SERVER ---

app = Flask(__name__)
CORS(app)  # Initialize CORS for the entire app. This allows all origins.

# This dictionary acts as our simple, in-memory database
# In a real app, this would be a real database (like Firebase or PostgreSQL)
USER_DATABASE = {}

@app.route('/onboard', methods=['POST'])
def onboard_user():
    """
    Endpoint to create a new user profile.
    Receives JSON data from the Lovable frontend.
    """
    data = request.json
    
    try:
        user = UserProfile(
            name=data['name'],
            age=data['age'],
            diagnosis_type=data['diagnosis_type'],
            years_since_diagnosis=data['years_since_diagnosis'],
            bmi=data['bmi'],
            on_metformin=data['on_metformin'],
            on_insulin=data['on_insulin']
        )
        
        # Save the user to our "database"
        USER_DATABASE[user.name] = user
        
        return jsonify({"message": f"User {user.name} created successfully!"}), 201
    
    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/add_log', methods=['POST'])
def add_log_and_predict():
    """
    Endpoint to add a daily log and get a prediction.
    This is the main "engine" endpoint.
    """
    data = request.json
    
    try:
        # 1. Find the user
        user_name = data['user_name']
        if user_name not in USER_DATABASE:
            return jsonify({"error": "User not found. Please onboard first."}), 404
        
        current_user = USER_DATABASE[user_name]
        
        # 2. Create the DailyLog object
        new_log = DailyLog(
            date=datetime.date.today(),
            sleep_hours=data['sleep_hours'],
            sleep_quality=data['sleep_quality'],
            carbs_g=data['carbs_g'],
            protein_g=data['protein_g'],
            fat_g=data['fat_g'],
            activity_minutes=data['activity_minutes'],
            took_metformin=data['took_metformin'],
            took_insulin=data['took_insulin']
        )
        current_user.logs.append(new_log)
        
        # 3. Run the AI Engine
        (risk, reason) = get_prediction_and_explanation(current_user, new_log)
        
        # 4. Generate Feedback
        suggestion = generate_personalized_feedback(current_user, new_log, risk, reason)
        
        # 5. Send the complete result back to Lovable
        return jsonify({
            "risk_score": risk,
            "risk_percentage": f"{risk*100:.0f}%",
            "explanation": reason,
            "suggestion": suggestion
        }), 200

    except KeyError as e:
        return jsonify({"error": f"Missing field: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/')
def home():
    """A simple route to check if the server is running."""
    return "GlucoFlow AI Engine is running."

# NOTE: The 'if __name__ == "__main__":' block
# has been REMOVED for Render deployment.
# Gunicorn will be used to run the 'app' object directly.
