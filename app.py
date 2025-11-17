import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

# --- [ NEW ] Helper functions to make our app "crash-proof" ---
# These will safely convert inputs, even if the frontend sends empty strings.

def safe_int(value, default=0):
    """Safely converts a value to an integer."""
    try:
        # Try to convert a float string (e..g, "5.0") to int first
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """Safely converts a value to a float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value):
    """Safely converts a value to a boolean."""
    # Handles "true", "True", "t", "1", "yes", "y"
    return str(value).lower() in ['true', 't', '1', 'yes', 'y']

# --- 1. DATA STRUCTURES (Now with "safe" inputs) ---

class UserProfile:
    """
    Holds the static, long-term data for a single user.
    """
    def __init__(self, name, age, diagnosis_type, years_since_diagnosis, bmi, on_metformin, on_insulin):
        # Demographics
        self.name = str(name)
        # [ --- MODIFIED --- ] Use safe conversion
        self.age = safe_int(age, 30) 
        
        # Clinical Profile
        self.diagnosis_type = str(diagnosis_type)
        self.years_since_diagnosis = safe_int(years_since_diagnosis, 0)
        self.bmi = safe_float(bmi, 25.0)
        
        # Medications
        self.on_metformin = safe_bool(on_metformin)
        self.on_insulin = safe_bool(on_insulin)
        
        self.logs = [] 

    def __repr__(self):
        return f"<UserProfile: {self.name}, {self.age}, {self.diagnosis_type}>"

class DailyLog:
    """
    Holds the dynamic, daily inputs from the user.
    [ --- UPGRADED --- ] Now includes stress and activity type.
    """
    def __init__(self, date, sleep_hours, sleep_quality, carbs_g, protein_g, fat_g, 
                 activity_minutes, activity_type, stress_level, # <-- NEW FIELDS
                 took_metformin, took_insulin):
        self.date = date
        
        # [ --- MODIFIED --- ] Use safe conversion for all inputs
        self.sleep_hours = safe_float(sleep_hours, 0)
        self.sleep_quality = str(sleep_quality)
        self.carbs_g = safe_int(carbs_g, 0)
        self.protein_g = safe_int(protein_g, 0)
        self.fat_g = safe_int(fat_g, 0)
        
        # [ --- MODIFIED --- ] New activity and stress fields
        self.activity_minutes = safe_int(activity_minutes, 0)
        self.activity_type = str(activity_type) # "none", "aerobic", "anaerobic"
        self.stress_level = str(stress_level) # "low", "medium", "high"
        
        # Medication Adherence
        self.took_metformin = safe_bool(took_metformin)
        self.took_insulin = safe_bool(took_insulin)

    def __repr__(self):
        return f"<DailyLog: {self.date.strftime('%Y-%m-%d')}, Carbs: {self.carbs_g}g>"

# --- 2. AI PREDICTION ENGINE (The "Smarter" Brain) ---

def get_prediction_and_explanation(user: UserProfile, log: DailyLog):
    """
    Simulates a trained ML model by analyzing the user's profile and latest log.
    [ --- UPGRADED --- ] Now understands stress, activity type, and balanced meals.
    """
    risk_score = 0.0
    explanation = {}
    
    # --- 1. Analyze Dietary Factors ---
    carb_risk = 0.0
    if log.carbs_g > 80:
        carb_risk = 0.40 
        risk_score += carb_risk
        explanation["High-Carb Meal ( > 80g)"] = carb_risk
    
    # --- [ NEW ] "Balanced Meal" Logic ---
    is_balanced_meal = log.protein_g > 15 or log.fat_g > 10
    if carb_risk > 0 and is_balanced_meal:
        balance_offset = -0.10  # A "protective" factor
        risk_score += balance_offset
        explanation["Balanced Meal Offset"] = balance_offset
    
    # --- 2. Analyze Lifestyle Factors ---
    if log.sleep_hours < 6:
        sleep_risk = 0.15
        risk_score += sleep_risk
        explanation["Poor Sleep ( < 6 hours)"] = sleep_risk
        
    # --- [ NEW ] Stress Logic ---
    if log.stress_level == "high":
        stress_risk = 0.20 # Stress is a significant factor
        risk_score += stress_risk
        explanation["High Stress Level"] = stress_risk
        
    # --- [ MODIFIED ] Activity Logic is now "smarter" ---
    if log.activity_minutes < 10:
        # Only add risk if no "post-meal" reward was given
        if "Post-Meal Aerobic Activity" not in explanation:
            activity_risk = 0.15
            risk_score += activity_risk
            explanation["Low Activity ( < 10 min)"] = activity_risk
    elif log.activity_type == "aerobic" and log.carbs_g > 50:
        # High reward for a walk after a high-carb meal
        activity_offset = -0.20
        risk_score += activity_offset
        explanation["Post-Meal Aerobic Activity"] = activity_offset
    elif log.activity_type == "anaerobic":
        # Smaller reward for anaerobic (still good!)
        activity_offset = -0.10
        risk_score += activity_offset
        explanation["Anaerobic Activity"] = activity_offset


    # --- 3. Analyze Personalized Clinical Factors ---
    if user.on_metformin and not log.took_metformin:
        metformin_risk = 0.30 
        risk_score += metformin_risk
        explanation["Missed Metformin Dose"] = metformin_risk
        
    if user.on_insulin and not log.took_insulin:
        insulin_risk = 0.50 
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
    # Ensure score is never below 0
    final_risk_score = max(0, risk_score)
    final_risk_score = min(final_risk_score, 1.0)
    
    return final_risk_score, explanation

# --- 3. PERSONALIZED FEEDBACK ENGINE (The "Smarter" Voice) ---

def generate_personalized_feedback(user: UserProfile, log: DailyLog, risk_score: float, explanation: dict):
    """
    [ --- UPGRADED --- ]
    Analyzes risk to generate QUANTITATIVE corrective and preventive suggestions.
    """
    
    # --- Heuristic Constants for Quantitative Feedback ---
    CARB_BASELINE = 60  # (g) Assumed "normal" carb load for a meal
    CARB_TO_WALK_RATIO = 1.0 # (min/g) 1 minute of walking offsets 1g of excess carbs
    
    # --- 1. Critical & High-Priority Feedback (Overrides all else) ---
    if "Missed Insulin Dose" in explanation:
        return ("**CRITICAL SUGGESTION:** You logged that you missed your insulin. "
                "This is the #1 reason for your high-risk score. Please follow your doctor's "
                "advice on what to do when you miss a dose.")

    if "Missed Metformin Dose" in explanation:
        return ("**HIGH PRIORITY SUGGESTION:** We noticed you may have missed your Metformin. "
                "This is a key factor in your risk today. "
                "Please try to set a reminder for your next dose.")

    # --- 2. High-Risk Corrective Feedback ---
    if risk_score > 0.6:
        # --- Quantitative Carb Suggestion ---
        if "High-Carb Meal ( > 80g)" in explanation and "Post-Meal Aerobic Activity" not in explanation:
            excess_carbs = log.carbs_g - CARB_BASELINE
            activity_suggestion_minutes = int(excess_carbs * CARB_TO_WALK_RATIO)
            
            # Clamp the suggestion to a reasonable amount
            activity_suggestion_minutes = max(15, min(activity_suggestion_minutes, 45)) 
            
            return (f"**HIGH RISK DETECTED.** Your carb load was high and un-managed by activity. "
                    f"**Corrective Action:** To help your body process these {log.carbs_g}g of carbs, "
                    f"a **{activity_suggestion_minutes}-minute aerobic walk** in the next hour is strongly recommended.")
        
        # --- Stress Suggestion ---
        if "High Stress Level" in explanation:
            return ("**HIGH RISK DETECTED.** You noted high stress. Stress (cortisol) "
                    "can directly raise blood sugar, even if you eat perfectly. "
                    "**Corrective Action:** Please take 5-10 minutes for a guided breathing exercise or a quiet walk. "
                    "Managing stress is key to managing glucose.")

    # --- 3. Moderate-Risk Corrective Feedback ---
    elif risk_score > 0.4:
        if "High-Carb Meal ( > 80g)" in explanation and "Balanced Meal Offset" not in explanation:
            return ("**MODERATE RISK.** Your meal was high in carbs and low in protein/fat. "
                    "**Corrective Action:** A quick 10-minute walk would be great. "
                    "**Preventive Tip:** For your next meal, try adding a source of protein (like chicken or beans) "
                    "to your carbs to help slow down sugar absorption.")
        
        if "Poor Sleep ( < 6 hours)" in explanation:
            return ("**MODERATE RISK.** You logged poor sleep. This can affect your "
                    "sugar levels all day. Your body may be more sensitive to carbs today. "
                    "**Preventive Tip:** Let's focus on planning for a good night's rest tonight.")

    # --- 4. Low-Risk Preventive & Positive Feedback ---
    else:
        # --- Preventive Tip (Even if score is low) ---
        if "High Stress Level" in explanation:
            return ("✅ **GREAT JOB!** Your risk score is low, *even though* you're under high stress. "
                    "You are managing it well! **Preventive Tip:** Remember that stress can build up. "
                    "Try to start tomorrow with 5 minutes of quiet time to stay ahead.")
                    
        if "Post-Meal Aerobic Activity" in explanation:
             return ("✅ **PERFECT STRATEGY!** You logged a high-carb meal *and* the aerobic activity "
                     "to manage it. This is exactly how to do it. Your risk score is low as a result. "
                     "Keep up the fantastic work!")
        
        # --- Default "All-Clear" ---
        return ("✅ **GREAT JOB!** Your risk score is low. "
                "Your logs show you're balancing your meals, activity, and medication well. "
                "You're doing fantastic!")

    # A default catch-all
    return "Please be mindful of your logged items. Try to balance your next meal and add some light activity."


# --- 4. FLASK API SERVER (Now "crash-proof") ---

app = Flask(__name__)
CORS(app)  # Initialize CORS for the entire app. This allows all origins.

# This dictionary acts as our simple, in-memory database
USER_DATABASE = {}

@app.route('/onboard', methods=['POST'])
def onboard_user():
    """
    Endpoint to create a new user profile.
    [ --- MODIFIED --- ] Now more robust to bad/missing data.
    """
    data = request.json
    
    try:
        # Check for minimum required field
        if 'name' not in data or not data['name']:
            return jsonify({"error": "Missing field: name is required"}), 400
            
        user = UserProfile(
            name=data.get('name'),
            age=data.get('age'),
            diagnosis_type=data.get('diagnosis_type'),
            years_since_diagnosis=data.get('years_since_diagnosis'),
            bmi=data.get('bmi'),
            on_metformin=data.get('on_metformin'),
            on_insulin=data.get('on_insulin')
        )
        
        USER_DATABASE[user.name] = user
        return jsonify({"message": f"User {user.name} created successfully!"}), 201
    
    except Exception as e:
        # Log the full error on the server for debugging
        print(f"Error in /onboard: {str(e)}")
        # Return a generic error to the user
        return jsonify({"error": f"An internal server error occurred."}), 500

@app.route('/add_log', methods=['POST'])
def add_log_and_predict():
    """
    Endpoint to add a daily log and get a prediction.
    [ --- MODIFIED --- ] Now accepts all new fields and is robust.
    """
    data = request.json
    
    try:
        # 1. Find the user
        user_name = data.get('user_name')
        if not user_name:
             return jsonify({"error": "Missing field: user_name is required"}), 400
        if user_name not in USER_DATABASE:
            return jsonify({"error": "User not found. Please onboard first."}), 404
        
        current_user = USER_DATABASE[user_name]
        
        # 2. Create the DailyLog object using safe .get()
        new_log = DailyLog(
            date=datetime.date.today(),
            sleep_hours=data.get('sleep_hours'),
            sleep_quality=data.get('sleep_quality'),
            carbs_g=data.get('carbs_g'),
            protein_g=data.get('protein_g'),
            fat_g=data.get('fat_g'),
            activity_minutes=data.get('activity_minutes'),
            activity_type=data.get('activity_type'),
            stress_level=data.get('stress_level'),
            took_metformin=data.get('took_metformin'),
            took_insulin=data.get('took_insulin')
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

    except Exception as e:
        # Log the full error on the server for debugging
        print(f"Error in /add_log: {str(e)}")
        # Return a generic error to the user
        return jsonify({"error": f"An internal server error occurred."}), 500

@app.route('/')
def home():
    """A simple route to check if the server is running."""
    return "GlucoFlow AI Engine is running."
