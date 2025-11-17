import streamlit as st
import datetime

# Helper Functions
def safe_int(value, default=0):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_bool(value):
    return str(value).lower() in ['true', 't', '1', 'yes', 'y']

# Data Classes
class UserProfile:
    def __init__(self, name, age, diagnosis_type, years_since_diagnosis, bmi, on_metformin, on_insulin):
        self.name = str(name)
        self.age = safe_int(age, 30) 
        self.diagnosis_type = str(diagnosis_type)
        self.years_since_diagnosis = safe_int(years_since_diagnosis, 0)
        self.bmi = safe_float(bmi, 25.0)
        self.on_metformin = safe_bool(on_metformin)
        self.on_insulin = safe_bool(on_insulin)
        self.logs = [] 

class DailyLog:
    def __init__(self, date, sleep_hours, sleep_quality, carbs_g, protein_g, fat_g, 
                 activity_minutes, activity_type, stress_level,
                 took_metformin, took_insulin):
        self.date = date
        self.sleep_hours = safe_float(sleep_hours, 0)
        self.sleep_quality = str(sleep_quality)
        self.carbs_g = safe_int(carbs_g, 0)
        self.protein_g = safe_int(protein_g, 0)
        self.fat_g = safe_int(fat_g, 0)
        self.activity_minutes = safe_int(activity_minutes, 0)
        self.activity_type = str(activity_type)
        self.stress_level = str(stress_level)
        self.took_metformin = safe_bool(took_metformin)
        self.took_insulin = safe_bool(took_insulin)

# AI Engine
def get_prediction_and_explanation(user: UserProfile, log: DailyLog):
    risk_score = 0.0
    explanation = {}
    
    # 1. Dietary Factors
    carb_risk = 0.0
    if log.carbs_g > 80:
        carb_risk = 0.40 
        risk_score += carb_risk
        explanation["High-Carb Meal ( > 80g)"] = carb_risk
    
    is_balanced_meal = log.protein_g > 15 or log.fat_g > 10
    if carb_risk > 0 and is_balanced_meal:
        balance_offset = -0.10
        risk_score += balance_offset
        explanation["Balanced Meal Offset"] = balance_offset
    
    # 2. Lifestyle Factors
    if log.sleep_hours < 6:
        sleep_risk = 0.15
        risk_score += sleep_risk
        explanation["Poor Sleep ( < 6 hours)"] = sleep_risk
        
    if log.stress_level == "high":
        stress_risk = 0.20
        risk_score += stress_risk
        explanation["High Stress Level"] = stress_risk
        
    if log.activity_minutes < 10:
        if "Post-Meal Aerobic Activity" not in explanation:
            activity_risk = 0.15
            risk_score += activity_risk
            explanation["Low Activity ( < 10 min)"] = activity_risk
    elif log.activity_type == "aerobic" and log.carbs_g > 50:
        activity_offset = -0.20
        risk_score += activity_offset
        explanation["Post-Meal Aerobic Activity"] = activity_offset
    elif log.activity_type == "anaerobic":
        activity_offset = -0.10
        risk_score += activity_offset
        explanation["Anaerobic Activity"] = activity_offset

    # 3. Clinical Factors
    if user.on_metformin and not log.took_metformin:
        metformin_risk = 0.30 
        risk_score += metformin_risk
        explanation["Missed Metformin Dose"] = metformin_risk
        
    if user.on_insulin and not log.took_insulin:
        insulin_risk = 0.50 
        risk_score += insulin_risk
        explanation["Missed Insulin Dose"] = insulin_risk
        
    # 4. Compounding Factors
    if user.bmi > 28 and risk_score > 0:
        bmi_amplifier = 0.10
        risk_score += bmi_amplifier
        explanation["Risk amplified by BMI"] = bmi_amplifier
        
    if user.years_since_diagnosis > 5 and risk_score > 0:
        duration_amplifier = 0.10
        risk_score += duration_amplifier
        explanation["Risk amplified by T2D duration"] = duration_amplifier

    # 5. Finalize Score
    final_risk_score = max(0, min(risk_score, 1.0))
    return final_risk_score, explanation

def generate_personalized_feedback(user: UserProfile, log: DailyLog, risk_score: float, explanation: dict):
    if "Missed Insulin Dose" in explanation:
        return ("CRITICAL: You logged that you missed your insulin. "
                "Please follow your doctor's advice on what to do "
                "when you miss a dose. This is the #1 reason for your high-risk score.")

    if "Missed Metformin Dose" in explanation:
        return ("HIGH PRIORITY: We noticed you may have missed your Metformin. "
                "This is a key factor in your risk today. "
                "Try to set a reminder for your next dose.")

    if "High Stress Level" in explanation and risk_score > 0.6:
        return ("Your risk score is high, and you noted high stress. Stress (cortisol) "
                "can directly raise blood sugar. "
                "**Actionable Suggestion:** Can you take 5 minutes for a guided breathing exercise?")

    if risk_score > 0.7:
        if "High-Carb Meal ( > 80g)" in explanation and "Low Activity ( < 10 min)" in explanation:
            return ("This is a high-risk combination... "
                    "**Actionable Suggestion:** Can you take a 15-20 minute aerobic walk? "
                    "This is the best way to help your body manage the carbs.")

        if "High-Carb Meal ( > 80g)" in explanation and "Poor Sleep ( < 6 hours)" in explanation:
            return ("Your risk is high. Poor sleep can make you more insulin resistant... "
                    "**Actionable Suggestion:** Be mindful of your next meal, "
                    "and let's focus on getting more rest tonight.")

    elif risk_score > 0.4:
        if "High-Carb Meal ( > 80g)" in explanation and "Balanced Meal Offset" not in explanation:
            return ("MODERATE RISK: Your meal was high in carbs and low in protein/fat. "
                    "**Pro-Tip:** Adding protein or healthy fats "
                    "to your carbs helps slow down sugar absorption. Try it for your next meal!")

        if "High-Carb Meal ( > 80g)" in explanation:
            return ("MODERATE RISK: Your meal was high in carbs. You did a good job balancing it... "
                    "but a quick 10-minute walk would still be a great way to help.")

        if "Poor Sleep ( < 6 hours)" in explanation:
            return ("MODERATE RISK: You logged poor sleep. This can affect your "
                    "sugar levels all day. Your body may be more sensitive to carbs today.")

    elif "Post-Meal Aerobic Activity" in explanation:
         return ("✅ FANTASTIC WORK! You logged a high-carb meal *and* the aerobic activity "
                 "to manage it. This is the perfect strategy! Your risk score is low as a result.")
    else:
        return ("✅ GREAT JOB! Your risk score is low. "
                "Keep up the fantastic work!")

    return "Please be mindful of your logged items, as they are contributing to a higher risk."

# Streamlit UI
st.set_page_config(layout="wide")

# Check if user_profile exists
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = None

# Page 1: Onboarding
if st.session_state.user_profile is None:
    st.title("Welcome to GlucoFlow! 🚀")
    
    with st.form("onboarding_form"):
        name = st.text_input("Name")
        age = st.number_input("Age", min_value=1, max_value=120, value=30)
        bmi = st.number_input("BMI", min_value=10.0, max_value=50.0, value=25.0, step=0.1)
        diagnosis = st.selectbox(
            "Diagnosis",
            ["Type 1 Diabetes", "Type 2 Diabetes", "Prediabetes", "Gestational Diabetes"]
        )
        years_since_diagnosis = st.number_input(
            "Years Since Diagnosis",
            min_value=0,
            max_value=100,
            value=0
        )
        on_metformin = st.checkbox("On Metformin")
        on_insulin = st.checkbox("On Insulin")
        
        submitted = st.form_submit_button("Create My Profile")
        
        if submitted:
            # Validate name
            if not name or name.strip() == "":
                st.error("Name cannot be empty. Please enter your name.")
            else:
                # Create UserProfile object
                user_profile = UserProfile(
                    name=name.strip(),
                    age=age,
                    diagnosis_type=diagnosis,
                    years_since_diagnosis=years_since_diagnosis,
                    bmi=bmi,
                    on_metformin=on_metformin,
                    on_insulin=on_insulin
                )
                
                # Save to session state
                st.session_state.user_profile = user_profile
                st.rerun()

# Page 2: Main Dashboard
else:
    user = st.session_state.user_profile
    
    # Sidebar
    with st.sidebar:
        st.write(f"Welcome, {user.name}!")
        if st.button("Reset User Profile (Logout)"):
            st.session_state.user_profile = None
            st.rerun()
    
    # Two-column layout
    col1, col2 = st.columns(2)
    
    # Column 1: Today's Log
    with col1:
        st.subheader("Today's Log")
        
        with st.form("log_form"):
            sleep_hours = st.number_input(
                "Sleep Hours",
                min_value=0.0,
                max_value=24.0,
                value=7.0,
                step=0.5
            )
            sleep_quality = st.selectbox(
                "Sleep Quality",
                ["Poor", "Fair", "Good", "Excellent"]
            )
            stress_level = st.selectbox(
                "Stress Level",
                ["Low", "Medium", "High"]
            )
            carbs_g = st.number_input(
                "Carbs (g)",
                min_value=0,
                max_value=1000,
                value=0
            )
            protein_g = st.number_input(
                "Protein (g)",
                min_value=0,
                max_value=1000,
                value=0
            )
            fat_g = st.number_input(
                "Fat (g)",
                min_value=0,
                max_value=1000,
                value=0
            )
            activity_minutes = st.number_input(
                "Activity (minutes)",
                min_value=0,
                max_value=1440,
                value=0
            )
            activity_type = st.selectbox(
                "Activity Type",
                ["None", "Aerobic", "Anaerobic"]
            )
            took_metformin = st.checkbox(
                "Took Metformin",
                disabled=not user.on_metformin
            )
            took_insulin = st.checkbox(
                "Took Insulin",
                disabled=not user.on_insulin
            )
            
            submitted = st.form_submit_button("Get My Forecast")
    
    # Column 2: AI-Powered Result
    with col2:
        st.subheader("Your AI-Powered Result")
        
        if submitted:
            # Create DailyLog object
            new_log = DailyLog(
                date=datetime.date.today(),
                sleep_hours=sleep_hours,
                sleep_quality=sleep_quality,
                carbs_g=carbs_g,
                protein_g=protein_g,
                fat_g=fat_g,
                activity_minutes=activity_minutes,
                activity_type=activity_type,
                stress_level=stress_level,
                took_metformin=took_metformin,
                took_insulin=took_insulin
            )
            
            # Call AI engine
            risk, reason = get_prediction_and_explanation(user, new_log)
            suggestion = generate_personalized_feedback(user, new_log, risk, reason)
            
            # Calculate risk percentage
            risk_percentage = f"{risk * 100:.0f}%"
            
            # Display risk and suggestion based on score
            if risk >= 0.7:
                st.error(f"**Risk Level: {risk_percentage}**")
                st.error(suggestion)
            elif risk >= 0.4:
                st.warning(f"**Risk Level: {risk_percentage}**")
                st.warning(suggestion)
            else:
                st.success(f"**Risk Level: {risk_percentage}**")
                st.success(suggestion)
            
            # Explainable AI
            with st.expander("See how we got this score"):
                st.write("**Explainable AI:**")
                
                # Sort by absolute value (descending)
                sorted_reason = sorted(
                    reason.items(),
                    key=lambda x: abs(x[1]),
                    reverse=True
                )
                
                for factor, impact in sorted_reason:
                    if impact > 0:
                        # Red for positive (bad) impacts
                        st.markdown(f'<span style="color: red;">🔴 **{factor}**: +{impact:.2f}</span>', 
                                  unsafe_allow_html=True)
                    else:
                        # Green for negative (good) impacts
                        st.markdown(f'<span style="color: green;">🟢 **{factor}**: {impact:.2f}</span>', 
                                  unsafe_allow_html=True)
        else:
            st.info("Please fill out your daily log...")
