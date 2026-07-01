"""
Streamlit Web Application for PlantPulse Guardian AI.
Provides a premium user interface to input soil and climate parameters,
trigger the multi-agent ADK workflow, and render analysis reports and history.
Supports bilingual English/Telugu interface, crop-aware fertilizer guides, and local assets.
"""

import sys
from pathlib import Path

# Fix python import path to make sure local package imports work correctly
current_dir = Path(__file__).parent.resolve()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

import streamlit as st
import asyncio
import os
import json
import time
from dotenv import load_dotenv

# Load local environment configurations (.env)
load_dotenv()

from google.adk.runners import InMemoryRunner

# Import existing agents
from src.agents.soil_agent import soil_agent
from src.agents.moisture_agent import moisture_agent
from src.agents.environment_agent import environment_agent
from src.agents.advisor_agent import advisor_agent

# Initialize session state variables
if "history" not in st.session_state:
    st.session_state.history = []
if "current_report" not in st.session_state:
    st.session_state.current_report = None
if "current_advice" not in st.session_state:
    st.session_state.current_advice = None

# Configure Streamlit page config
st.set_page_config(
    page_title="PlantPulse Guardian AI",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Bilingual Translation Mappings & Localization
# ---------------------------------------------------------
TRANSLATIONS = {
    "English": {
        "title": "PlantPulse Guardian AI",
        "subtitle": "AI-Powered Multi-Agent Agriculture Advisor",
        "built_with": "Built using Google ADK | Gemini | Streamlit",
        "language_label": "Choose Language / భాషను ఎంచుకోండి",
        "how_it_works_title": "📖 How It Works",
        "step_1": "Step 1: Enter Soil & Climate Data",
        "step_1_desc": "Provide current sensor readings (N, P, K, Temp, Humidity, Moisture).",
        "step_2": "Step 2: Domain Agents Analyze",
        "step_2_desc": "Specialist agents analyze soil nutrition, soil moisture, and atmospheric conditions.",
        "step_3": "Step 3: Coordinator Compiles",
        "step_3_desc": "The Farm Advisor Agent consolidates all metrics into a unified advisory plan.",
        "step_4": "Step 4: Receive Farmer Advice",
        "step_4_desc": "Get simple, actionable instructions and crop-aware fertilizer guides.",
        "sensor_readings": "📊 Field Sensor Readings",
        "crop_select": "Select Crop to Analyze",
        "n_label": "Nitrogen (N) (mg/kg)",
        "p_label": "Phosphorus (P) (mg/kg)",
        "k_label": "Potassium (K) (mg/kg)",
        "temp_label": "Temperature (°C)",
        "humid_label": "Humidity (%)",
        "moist_label": "Soil Moisture (%)",
        "weather_forecast_label": "Optional Weather Forecast / Local Conditions",
        "actions": "Actions",
        "analyze_btn": "🚀 Analyze Crop",
        "reset_btn": "↩️ Reset Dashboard",
        "history_title": "📜 Analysis History",
        "reopen_report": "Reopen Past Reports",
        "no_history": "No past reports in history.",
        "offline_notice": "💡 Note: Running in Offline Local Rule-Based mode since GEMINI_API_KEY is not configured.",
        "running_soil": "🔬 Soil Agent Running...",
        "running_moisture": "💧 Moisture Agent Running...",
        "running_env": "🌦 Environment Agent Running...",
        "running_advisor": "🤖 Advisor Agent Running...",
        "analysis_complete": "✅ Analysis Complete!",
        "health_score_title": "Overall Plant Health Score",
        "risk_level_title": "Overall Risk Level",
        "farmer_friendly_sec": "🧑‍🌾 Farmer-Friendly Advice",
        "tech_report_sec": "🔬 Technical AI Report",
        "soil_analysis": "Soil Analysis",
        "environment_analysis": "Environmental Analysis",
        "moisture_analysis": "Moisture Analysis",
        "ai_recommendation": "AI Recommendation",
        "fertilizer_rec_title": "🌾 Fertilizer Recommendations & Application Guide",
        "fertilizer_notice": "⚠️ Note: Exact quantity depends on the specific crop variety and soil-test results.",
        "download_title": "📥 Download Advisory Reports",
        "dl_json": "Download JSON Report",
        "dl_pdf": "Download PDF Report",
        "footer_text": "Developed for Kaggle AI Agents Capstone",
        
        # Farmer friendly advice questions
        "q_problem": "What is the problem?",
        "q_why": "Why did it happen?",
        "q_do": "What should you do?",
        "q_fert": "Which fertilizer should be used?",
        "q_when": "When should it be applied?",
        "q_prec": "What precautions should you take?",
        
        "optimal_health": "Your crop is in optimal health. No major issues detected.",
        "optimal_moisture": "Soil moisture is in the optimal range. No irrigation required.",
        "optimal_env": "Ambient temperature and humidity are optimal. No climate stress.",
        "Low": "Low",
        "Medium": "Medium",
        "High": "High",
    },
    "Telugu": {
        "title": "ప్లాంట్‌పల్స్ గార్డియన్ AI",
        "subtitle": "AI-ఆధారిత మల్టీ-ఏజెంట్ వ్యవసాయ సలహాదారు",
        "built_with": "గూగుల్ ADK | జెమిని | స్ట్రీమ్‌లిట్‌తో నిర్మించబడింది",
        "language_label": "భాషను ఎంచుకోండి / Choose Language",
        "how_it_works_title": "📖 ఇది ఎలా పనిచేస్తుంది",
        "step_1": "దశ 1: నేల & వాతావరణ సమాచారాన్ని నమోదు చేయండి",
        "step_1_desc": "ప్రస్తుత సెన్సార్ రీడింగ్‌లను (N, P, K, ఉష్ణోగ్రత, తేమ) అందించండి.",
        "step_2": "దశ 2: నిపుణుల ఏజెంట్ల విశ్లేషణ",
        "step_2_desc": "నేల పోషకాలు, నేల తేమ మరియు వాతావరణ పరిస్థితులను వేర్వేరు ఏజెంట్లు విశ్లేషిస్తాయి.",
        "step_3": "దశ 3: సమన్వయకర్త నివేదిక తయారీ",
        "step_3_desc": "ఫామ్ అడ్వైజర్ ఏజెంట్ అన్ని విశ్లేషణలను కలిపి ఒక సమగ్ర నివేదికను తయారు చేస్తుంది.",
        "step_4": "దశ 4: రైతు సలహా పొందండి",
        "step_4_desc": "సులభమైన, ఆచరణాత్మక సూచనలు మరియు ఎరువుల మార్గదర్శకాలను పొందండి.",
        "sensor_readings": "📊 నేల మరియు వాతావరణ రీడింగ్‌లు",
        "crop_select": "పంటను ఎంచుకోండి",
        "n_label": "నత్రజని (Nitrogen - N) (mg/kg)",
        "p_label": "భాస్వరం (Phosphorus - P) (mg/kg)",
        "k_label": "పొటాషియం (Potassium - K) (mg/kg)",
        "temp_label": "ఉష్ణోగ్రత (Temperature) (°C)",
        "humid_label": "గాలిలో తేమ (Humidity) (%)",
        "moist_label": "నేల తేమ (Soil Moisture) (%)",
        "weather_forecast_label": "వాతావరణ సూచన (ఐచ్ఛికం) / స్థానిక పరిస్థితులు",
        "actions": "చర్యలు",
        "analyze_btn": "🚀 పంటను విశ్లేషించండి",
        "reset_btn": "↩️ రీసెట్ చేయండి",
        "history_title": "📜 పాత విశ్లేషణల చరిత్ర",
        "reopen_report": "పాత నివేదికలను చూడండి",
        "no_history": "చరిత్రలో పాత నివేదికలు లేవు.",
        "offline_notice": "💡 గమనిక: GEMINI_API_KEY కాన్ఫిగర్ చేయనందున ఆఫ్‌లైన్ లోకల్ రూల్-బేస్డ్ మోడ్‌లో రన్ అవుతోంది.",
        "running_soil": "🔬 నేల విశ్లేషణ ఏజెంట్ రన్ అవుతోంది...",
        "running_moisture": "💧 నేల తేమ విశ్లేషణ ఏజెంట్ రన్ అవుతోంది...",
        "running_env": "🌦 వాతావరణ విశ్లేషణ ఏజెంట్ రన్ అవుతోంది...",
        "running_advisor": "🤖 ఫామ్ అడ్వైజర్ ఏజెంట్ రన్ అవుతోంది...",
        "analysis_complete": "✅ విశ్లేషణ పూర్తయింది!",
        "health_score_title": "మొక్కల మొత్తం ఆరోగ్య స్కోరు",
        "risk_level_title": "మొత్తం ప్రమాద స్థాయి",
        "farmer_friendly_sec": "🧑‍🌾 రైతు స్నేహపూర్వక సలహాలు",
        "tech_report_sec": "🔬 సాంకేతిక AI నివేదిక",
        "soil_analysis": "నేల విశ్లేషణ",
        "environment_analysis": "పర్యావరణ విశ్లేషణ",
        "moisture_analysis": "నేల తేమ విశ్లేషణ",
        "ai_recommendation": "AI సిఫార్సులు",
        "fertilizer_rec_title": "🌾 ఎరువుల సిఫార్సులు & వాడే విధానం",
        "fertilizer_notice": "⚠️ గమనిక: సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది.",
        "download_title": "📥 నివేదికలను డౌన్‌లోడ్ చేయండి",
        "dl_json": "JSON నివేదికను డౌన్‌లోడ్ చేయండి",
        "dl_pdf": "PDF నివేదికను డౌన్‌లోడ్ చేయండి",
        "footer_text": "కాగిల్ AI ఏజెంట్స్ క్యాప్‌స్టోన్ కోసం అభివృద్ధి చేయబడింది",
        
        # Farmer friendly advice questions
        "q_problem": "సమస్య ఏమిటి?",
        "q_why": "ఇది ఎందుకు జరిగింది?",
        "q_do": "రైతు ఏమి చేయాలి?",
        "q_fert": "ఏ ఎరువులు వాడాలి?",
        "q_when": "ఎప్పుడు వేయాలి?",
        "q_prec": "ఎటువంటి జాగ్రత్తలు తీసుకోవాలి?",
        
        "optimal_health": "మీ పంట చాలా ఆరోగ్యంగా ఉంది. ఎటువంటి సమస్యలు లేవు.",
        "optimal_moisture": "నేల తేమ సరిగ్గా ఉంది. నీరు పెట్టాల్సిన అవసరం లేదు.",
        "optimal_env": "ఉష్ణోగ్రత మరియు గాలిలో తేమ అనుకూలంగా ఉన్నాయి. ఎటువంటి శీతోష్ణస్థితి ఒత్తిడి లేదు.",
        "Low": "తక్కువ",
        "Medium": "మధ్యస్థ",
        "High": "అధిక",
    }
}

# ---------------------------------------------------------
# Custom Styling (Theme-Aware CSS Injection)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');

    /* Global Typography setting */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Outfit', sans-serif;
    }

    /* Page Fade-in animation */
    .main-container {
        animation: fadeIn 0.8s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Theme-Aware Premium Glassmorphic Cards */
    .metric-card {
        background: rgba(128, 128, 128, 0.06);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(128, 128, 128, 0.15);
        border-radius: 16px;
        padding: 24px;
        margin: 12px 0px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.04);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        color: var(--text-color);
    }

    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(76, 175, 80, 0.15);
        border: 1px solid rgba(76, 175, 80, 0.4);
    }

    /* Card Titles */
    .metric-card h3 {
        color: var(--primary-color) !important;
        border-bottom: 2px solid rgba(76, 175, 80, 0.2);
        padding-bottom: 8px;
        margin-top: 0px;
    }

    /* Status Badges */
    .badge {
        padding: 8px 20px;
        border-radius: 30px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        min-width: 120px;
    }
    
    .badge-low {
        background-color: rgba(46, 125, 50, 0.15);
        color: #4caf50;
        border: 1px solid rgba(46, 125, 50, 0.3);
    }

    .badge-medium {
        background-color: rgba(239, 108, 0, 0.15);
        color: #ff9800;
        border: 1px solid rgba(239, 108, 0, 0.3);
    }

    .badge-high {
        background-color: rgba(198, 40, 40, 0.15);
        color: #f44336;
        border: 1px solid rgba(198, 40, 40, 0.3);
    }
    
    /* Custom button styling overrides */
    div.stButton > button {
        background-color: #1b5e20 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.3s !important;
    }
    
    div.stButton > button:hover {
        background-color: #2e7d32 !important;
        transform: scale(1.02) !important;
        box-shadow: 0 4px 12px rgba(76, 175, 80, 0.3) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------------------------------------
# Dynamic Translation & Fallback Logic
# ---------------------------------------------------------
STATIC_TELUGU_TRANSLATIONS = {
    
    "Low Nitrogen": "నేలలో నత్రజని (Nitrogen) శాతం తక్కువగా ఉంది.",
    "High Nitrogen": "నేలలో నత్రజని (Nitrogen) శాతం ఎక్కువగా ఉంది.",
    "Low Phosphorus": "నేలలో భాస్వరం (Phosphorus) శాతం తక్కువగా ఉంది.",
    "High Phosphorus": "నేలలో భాస్వరం (Phosphorus) శాతం ఎక్కువగా ఉంది.",
    "Low Potassium": "నేలలో పొటాషియం (Potassium) శాతం తక్కువగా ఉంది.",
    "High Potassium": "నేలలో పొటాషియం (Potassium) శాతం ఎక్కువగా ఉంది.",
    "Soil is critically dry": "నేల చాలా ఎండిపోయింది.",
    "Soil moisture levels are low": "నేలలో తేమ తక్కువగా ఉంది.",
    "Soil moisture is elevated": "నేలలో తేమ ఎక్కువగా ఉంది.",
    "Soil is waterlogged": "నేల బురదగా మారింది (నీరు ఎక్కువగా నిలిచింది).",
    "Cold Stress": "చలి ఒత్తిడి (తక్కువ ఉష్ణోగ్రత).",
    "Heat Stress": "వేడి ఒత్తిడి (ఎక్కువ ఉష్ణోగ్రత).",
    "Dry Air Stress": "గాలిలో తేమ చాలా తక్కువగా ఉంది.",
    "High disease risk": "పంట తెగుళ్ల వచ్చే అవకాశం ఎక్కువగా ఉంది.",
    "Apply nitrogen-rich fertilizer (e.g., urea, ammonium nitrate) or organic compost.": "నత్రజని ఎరువులు (యూరియా లేదా పశువుల ఎరువు) వేయండి.",
    "Apply potash, kelp meal, or potassium sulfate.": "పొటాష్ లేదా పొటాషియం సల్ఫేట్ వేయండి.",
    "Apply bone meal, rock phosphate, or phosphate-heavy synthetic fertilizer.": "డి.ఎ.పి (DAP) లేదా సింగిల్ సూపర్ ఫాస్ఫేట్ వేయండి.",
    "Initiate deep irrigation immediately. Check for drip irrigation system blocks.": "వెంటనే నీరు పెట్టండి. డ్రిప్ సిస్టమ్ సరిగ్గా ఉందో లేదో చూడండి.",
    "Schedule irrigation. Monitor moisture trends.": "నీరు పెట్టడానికి ప్రణాళిక వేసుకోండి.",
    "Disable irrigation. Improve soil drainage to prevent root rot.": "నీరు పెట్టడం ఆపివేయండి. నీరు బయటకు పోయేలా కాలువలు తీయండి.",
    "Implement frost protection covers or thermal sheeting.": "పంటపై కప్పే దుప్పట్లు లేదా షీట్లు వాడండి.",
    "Apply shading nets. Spray water during cooler hours to lower temperature.": "నీడ నిచ్చే నెట్లు వాడండి. చల్లని వేళల్లో నీరు పిచికారీ చేయండి.",
    "Improve spacing and ventilation to mitigate fungal blight or powdery mildew.": "గాలి బాగా ఆడేలా చూడండి. బూజు తెగులు రాకుండా మందు పిచికారీ చేయండి.",
}

def translate_text(text: str, target_lang: str) -> str:
    """Translates dynamic text using Gemini or static dictionaries."""
    if target_lang == "English":
        return text
        
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return STATIC_TELUGU_TRANSLATIONS.get(text, text)
        
    try:
        from google import genai
        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                f"Translate this agricultural report item into simple, clear Telugu (in Telugu script). "
                f"Use words that a local farmer who only speaks Telugu can easily understand. "
                f"Keep it short, direct, and actionable. Do not add markdown headers. Translate this text:\n\n{text}"
            )
        )
        return response.text.strip()
    except Exception:
        return STATIC_TELUGU_TRANSLATIONS.get(text, text)


# ---------------------------------------------------------
# Crop-Aware Fertilizer Database
# ---------------------------------------------------------
FERTILIZER_DB = {
    "Urea": {
        "image": "assets/urea.png",
        "names": {"English": "Urea", "Telugu": "యూరియా"},
        "purpose": {
            "English": "Promotes green vegetative growth and leaf development.",
            "Telugu": "ఆకుపచ్చటి ఆకుల పెరుగుదలకు మరియు మొక్కల ఎదుగుదలకు సహాయపడుతుంది."
        },
        "why": {
            "English": "Soil is deficient in Nitrogen.",
            "Telugu": "నేలలో నత్రజని (Nitrogen) లోపం ఉన్నందున సిఫార్సు చేయబడింది."
        },
        "guidance": {
            "English": "Apply 50-100 kg per acre. The exact quantity depends on the crop and soil-test recommendations.",
            "Telugu": "ఎకరానికి 50-100 కిలోలు వేయండి. సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది."
        },
        "time": {
            "English": "During the active vegetative growth phase.",
            "Telugu": "మొక్కల ఎదుగుదల దశలో (వెజిటేటివ్ దశ)."
        },
        "precautions": {
            "English": "Avoid applying on wet leaves to prevent leaf burn. Water the field immediately after application.",
            "Telugu": "ఆకులు తడిగా ఉన్నప్పుడు వేయకండి (ఆకులు మాడిపోతాయి). వేసిన వెంటనే పొలానికి నీరు పెట్టండి."
        }
    },
    "DAP": {
        "image": "assets/dap.png",
        "names": {"English": "DAP (Di-Ammonium Phosphate)", "Telugu": "డి.ఎ.పి (DAP)"},
        "purpose": {
            "English": "Provides essential phosphorus for root development and early growth.",
            "Telugu": "వేర్ల బలానికి మరియు ప్రారంభ ఎదుగుదలకు అవసరమైన భాస్వరం అందిస్తుంది."
        },
        "why": {
            "English": "Soil is deficient in Phosphorus.",
            "Telugu": "నేలలో భాస్వరం (Phosphorus) లోపం ఉన్నందున సిఫార్సు చేయబడింది."
        },
        "guidance": {
            "English": "Apply 40-50 kg per acre at sowing or transplanting. The exact quantity depends on the crop and soil-test recommendations.",
            "Telugu": "విత్తే సమయంలో లేదా నాటే సమయంలో ఎకరానికి 40-50 కిలోలు వేయండి. సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది."
        },
        "time": {
            "English": "At the time of sowing or transplanting (Basal application).",
            "Telugu": "విత్తేటప్పుడు లేదా నాటేటప్పుడు (బేసల్ అప్లికేషన్)."
        },
        "precautions": {
            "English": "Place fertilizer 2 inches below and beside seeds to avoid damage.",
            "Telugu": "విత్తనాలకు తగలకుండా కొంచెం దూరంలో (2 అంగుళాలు) వేయండి."
        }
    },
    "MOP": {
        "image": "assets/mop.png",
        "names": {"English": "MOP (Muriate of Potash)", "Telugu": "పొటాష్ (MOP)"},
        "purpose": {
            "English": "Improves disease resistance, stalk strength, and fruit quality.",
            "Telugu": "రోగా నిరోధక శక్తిని, కాండం బలాన్ని మరియు పండ్ల నాణ్యతను పెంచుతుంది."
        },
        "why": {
            "English": "Soil is deficient in Potassium.",
            "Telugu": "నేలలో పొటాషియం (Potassium) లోపం ఉన్నందున సిఫార్సు చేయబడింది."
        },
        "guidance": {
            "English": "Apply 25-40 kg per acre. The exact quantity depends on the crop and soil-test recommendations.",
            "Telugu": "ఎకరానికి 25-40 కిలోలు వేయండి. సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది."
        },
        "time": {
            "English": "During tillering or flower initiation stages.",
            "Telugu": "పిలకలు వచ్చే దశలో లేదా పూత వచ్చే దశలో వేయండి."
        },
        "precautions": {
            "English": "Avoid applying in highly saline soils. Water after application.",
            "Telugu": "చవిటి నేలల్లో వాడకండి. వేసిన వెంటనే నీరు పెట్టండి."
        }
    },
    "SSP": {
        "image": "assets/ssp.png",
        "names": {"English": "SSP (Single Super Phosphate)", "Telugu": "సూపర్ ఫాస్ఫేట్ (SSP)"},
        "purpose": {
            "English": "Supplies phosphorus, sulphur, and calcium for optimal crop health.",
            "Telugu": "మొక్కల ఎదుగుదలకు అవసరమైన భాస్వరం, గంధకం మరియు కాల్షియంలను అందిస్తుంది."
        },
        "why": {
            "English": "Soil is deficient in Phosphorus and sulphur.",
            "Telugu": "నేలలో భాస్వరం మరియు గంధకం లోపం ఉన్నందున సిఫార్సు చేయబడింది."
        },
        "guidance": {
            "English": "Apply 100-150 kg per acre as basal dose. The exact quantity depends on the crop and soil-test recommendations.",
            "Telugu": "ఎకరానికి 100-150 కిలోలు బేసల్ డోస్‌గా వేయండి. సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది."
        },
        "time": {
            "English": "During final land preparation before planting.",
            "Telugu": "చివరి దుక్కిలో నాటడానికి ముందు వేయండి."
        },
        "precautions": {
            "English": "Do not mix SSP with Urea long before application; mix only at application time.",
            "Telugu": "యూరియాతో కలిపి ఎక్కువ సేపు ఉంచకండి; చల్లే సమయంలో మాత్రమే కలపండి."
        }
    },
    "Calcium Nitrate": {
        "image": "assets/calcium_nitrate.png",
        "names": {"English": "Calcium Nitrate", "Telugu": "కాల్షియం నైట్రేట్"},
        "purpose": {
            "English": "Improves fruit quality and prevents blossom-end rot in vegetables.",
            "Telugu": "పండ్ల నాణ్యతను పెంచుతుంది మరియు కూరగాయలలో కుళ్లు తెగులు (blossom-end rot) నివారిస్తుంది."
        },
        "why": {
            "English": "Highly recommended for fruiting crops (like Tomato) to boost calcium.",
            "Telugu": "టమాటా వంటి పండ్ల పంటలలో కాల్షియం మరియు నత్రజని పెంచడానికి సిఫార్సు చేయబడింది."
        },
        "guidance": {
            "English": "Apply 25-50 kg per acre. The exact quantity depends on the crop and soil-test recommendations.",
            "Telugu": "ఎకరానికి 25-50 కిలోలు వేయండి. సరైన పరిమాణం పంట రకం మరియు నేల పరీక్ష ఫలితాలపై ఆధారపడి ఉంటుంది."
        },
        "time": {
            "English": "During the flowering and fruit-setting stages.",
            "Telugu": "పూత మరియు కాయలు కాసే దశలో వేయండి."
        },
        "precautions": {
            "English": "Store in dry place as it absorbs atmospheric moisture quickly.",
            "Telugu": "ఇది తేమను త్వరగా పీల్చుకుంటుంది, పొడిగా ఉండే ప్రదేశంలో నిల్వ చేయండి."
        }
    }
}

def get_recommended_fertilizers(crop_name: str, soil_issues: list) -> list:
    """Returns dynamic, crop-aware fertilizer recommendations based on soil issues."""
    crop = crop_name.lower()
    has_n = any("nitrogen" in x.lower() or "n" in x.lower() for x in soil_issues)
    has_p = any("phosphorus" in x.lower() or "p" in x.lower() for x in soil_issues)
    has_k = any("potassium" in x.lower() or "k" in x.lower() for x in soil_issues)
    
    recommended = []
    
    if crop == "rice":
        if has_n: recommended.append("Urea")
        if has_p: recommended.append("DAP")
        if has_k: recommended.append("MOP")
    elif crop == "tomato":
        if has_n: 
            recommended.append("Calcium Nitrate")
            recommended.append("Urea")
        if has_k: recommended.append("MOP")
    elif crop == "maize":
        if has_n: recommended.append("Urea")
        if has_p: recommended.append("DAP")
    elif crop == "chilli":
        if has_p: recommended.append("DAP")
        if has_k: recommended.append("MOP")
    elif crop == "mango":
        if has_n: recommended.append("Urea")
        if has_p: recommended.append("DAP")
        if has_k: recommended.append("MOP")
    else:
        # Default mapping for Cotton, Wheat, Apple, Banana, Sugarcane
        if has_n: recommended.append("Urea")
        if has_p: recommended.append("DAP")
        if has_k: recommended.append("MOP")
        
    return recommended

# ---------------------------------------------------------
# Dynamic Farmer-Friendly AI Reasoning
# ---------------------------------------------------------
def get_ai_farmer_advice(report: dict, lang: str) -> dict:
    """Calls Gemini to generate structured, simplified farmer-friendly advice."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return local_rule_fallback(report["crop_name"], **report["inputs"])["advisor"] # Use local advisor fallback
        
    try:
        from google import genai
        client = genai.Client()
        
        summary = (
            f"Crop: {report['crop_name']}\n"
            f"Soil Issues: {report['soil']['issues']}\n"
            f"Moisture Status: {report['moisture']['moisture_status']}, Issues: {report['moisture']['issues']}\n"
            f"Environment Issues: {report['environment']['issues']}\n"
            f"AI Recommendation: {report['advisor']['final_recommendation']}\n"
        )
        
        prompt = (
            f"You are a friendly agriculture officer. Based on these crop diagnostic metrics, generate a simple, "
            f"farmer-friendly advice report answering these exact 6 questions in simple terms (avoid complex jargon):\n"
            f"1. What is the problem?\n"
            f"2. Why did it happen?\n"
            f"3. What should the farmer do?\n"
            f"4. Which fertilizer should be used?\n"
            f"5. When should it be applied?\n"
            f"6. What precautions should be taken?\n\n"
            f"Return a JSON object with keys: 'problem', 'why', 'what_to_do', 'fertilizer', 'when_to_apply', 'precautions'. "
            f"The values must be short, clear bullet points or single sentences. "
            f"Language requirement: Output the values in {'Telugu' if lang == 'Telugu' else 'English'}."
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[summary, prompt],
            config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text.strip())
    except Exception:
        # Static fallback
        return generate_static_farmer_advice(report, lang)


def generate_static_farmer_advice(report: dict, lang: str) -> dict:
    """Fallback static advice block generator."""
    t = TRANSLATIONS[lang]
    soil_issues = report["soil"]["issues"]
    moist_issues = report["moisture"]["issues"]
    env_issues = report["environment"]["issues"]
    
    all_issues = soil_issues + moist_issues + env_issues
    if not all_issues:
        prob = t["optimal_health"]
        why = "Good weather and proper maintenance." if lang == "English" else "మంచి వాతావరణం మరియు సరైన నిర్వహణ."
        todo = "Continue current farming practices." if lang == "English" else "ప్రస్తుత వ్యవసాయ పద్ధతులను కొనసాగించండి."
        fert = "No fertilizer required at this stage." if lang == "English" else "ఈ దశలో ఎరువులు అవసరం లేదు."
        when = "N/A"
        prec = "Keep monitoring regularly." if lang == "English" else "క్రమం తప్పకుండా పంటను పరిశీలిస్తూ ఉండండి."
    else:
        if lang == "Telugu":
            prob = "నేల మరియు శీతోష్ణస్థితిలో లోపాలు ఉన్నాయి: " + ", ".join([translate_text(x, "Telugu") for x in all_issues])
            why = "పోషకాల కొరత మరియు వాతావరణ మార్పుల వల్ల జరిగింది."
            todo = "సిఫార్సు చేసిన ఎరువులను వేయండి మరియు పొలానికి సమయానికి నీరు పెట్టండి."
            
            ferts = []
            if report["soil"]["soil_score"] < 100:
                if any("nitrogen" in x.lower() or "n" in x.lower() for x in soil_issues):
                    ferts.append("యూరియా (Urea) లేదా అమ్మోనియం సల్ఫేట్")
                if any("phosphorus" in x.lower() or "p" in x.lower() for x in soil_issues):
                    ferts.append("డి.ఎ.పి (DAP) లేదా సూపర్ ఫాస్ఫేట్")
                if any("potassium" in x.lower() or "k" in x.lower() for x in soil_issues):
                    ferts.append("పొటాష్ (MOP)")
            fert = ", ".join(ferts) if ferts else "ఎరువులు అవసరం లేదు"
            when = "ఉదయం లేదా సాయంత్రం వేళల్లో వేయండి."
            prec = "తడి ఆకులపై ఎరువులు వేయకండి, వేసిన వెంటనే నీరు పెట్టండి."
        else:
            prob = "Soil and climate issues: " + ", ".join(all_issues)
            why = "Lack of nutrient replenishment and fluctuating weather conditions."
            todo = "Apply recommended fertilizers and adjust irrigation schedules."
            ferts = []
            if report["soil"]["soil_score"] < 100:
                if any("nitrogen" in x.lower() or "n" in x.lower() for x in soil_issues):
                    ferts.append("Urea or Ammonium Sulphate")
                if any("phosphorus" in x.lower() or "p" in x.lower() for x in soil_issues):
                    ferts.append("DAP or SSP")
                if any("potassium" in x.lower() or "k" in x.lower() for x in soil_issues):
                    ferts.append("MOP (Potash)")
            fert = ", ".join(ferts) if ferts else "No fertilizer needed."
            when = "During early morning or late afternoon when temperature is low."
            prec = "Avoid leaf contact, water the field immediately after application."
            
    return {
        "problem": prob,
        "why": why,
        "what_to_do": todo,
        "fertilizer": fert,
        "when_to_apply": when,
        "precautions": prec
    }


def extract_output_from_events(events: list) -> dict:
    """Extracts the structured output dictionary from a list of ADK Event objects."""
    if not events:
        raise ValueError("No events returned from the agent execution.")
        
    for event in reversed(events):
        if hasattr(event, "output") and event.output is not None:
            if hasattr(event.output, "model_dump"):
                return event.output.model_dump()
            if hasattr(event.output, "dict"):
                return event.output.dict()
            if isinstance(event.output, dict):
                return event.output
                
    for event in reversed(events):
        text_content = ""
        if hasattr(event, "content") and event.content:
            parts = getattr(event.content, "parts", []) or []
            text_content = "".join([part.text for part in parts if hasattr(part, "text") and part.text])
        elif hasattr(event, "message") and event.message:
            parts = getattr(event.message, "parts", []) or []
            text_content = "".join([part.text for part in parts if hasattr(part, "text") and part.text])
            
        text_content = text_content.strip()
        if text_content:
            if text_content.startswith("```"):
                lines = text_content.split("\n")
                if lines[0].strip().startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip().startswith("```"):
                    lines = lines[:-1]
                text_content = "\n".join(lines).strip()
                
            try:
                return json.loads(text_content)
            except Exception:
                import re
                match = re.search(r"\{.*\}", text_content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(0))
                    except Exception:
                        pass
                        
    raise ValueError("Could not locate any valid structured JSON output in the agent event history.")


def local_rule_fallback(crop_name: str, n: int, p: int, k: int, temp: float, humid: int, moist: int) -> dict:
    """Fallback rule-based diagnostic in case the Gemini API key is missing or calls fail."""
    # 1. Soil Fallback
    soil_issues = []
    soil_recs = []
    soil_score = 100
    
    if n < 40:
        soil_issues.append("Low Nitrogen (N) levels detected.")
        soil_recs.append("Apply nitrogen-rich fertilizer (e.g., urea, ammonium nitrate) or organic compost.")
        soil_score -= 15
    elif n > 60:
        soil_issues.append("High Nitrogen (N) levels detected.")
        soil_recs.append("Reduce nitrogen application. Flush soil with clean water if necessary.")
        soil_score -= 10
        
    if p < 20:
        soil_issues.append("Low Phosphorus (P) levels detected.")
        soil_recs.append("Apply bone meal, rock phosphate, or phosphate-heavy synthetic fertilizer.")
        soil_score -= 15
    elif p > 30:
        soil_issues.append("High Phosphorus (P) levels detected.")
        soil_recs.append("Discontinue phosphate fertilizers. High P can block uptake of micronutrients.")
        soil_score -= 10
        
    if k < 30:
        soil_issues.append("Low Potassium (K) levels detected.")
        soil_recs.append("Apply potash, kelp meal, or potassium sulfate.")
        soil_score -= 15
    elif k > 50:
        soil_issues.append("High Potassium (K) levels detected.")
        soil_recs.append("Avoid potassium supplements. High K interferes with calcium absorption.")
        soil_score -= 10
        
    soil_score = max(0, soil_score)

    # 2. Moisture Fallback
    moist_status = "Optimal"
    moist_issues = []
    moist_recs = []
    moist_score = 100
    
    if moist < 20:
        moist_status = "Very Dry"
        moist_issues.append("Soil is critically dry.")
        moist_recs.append("Initiate deep irrigation immediately. Check for drip irrigation system blocks.")
        moist_score = 30
    elif moist <= 40:
        moist_status = "Dry"
        moist_issues.append("Soil moisture levels are low.")
        moist_recs.append("Schedule irrigation. Monitor moisture trends.")
        moist_score = 70
    elif moist <= 70:
        moist_status = "Optimal"
        moist_recs.append("No immediate watering required. Optimal moisture balance.")
        moist_score = 100
    elif moist <= 85:
        moist_status = "Wet"
        moist_issues.append("Soil moisture is elevated.")
        moist_recs.append("Delay next watering cycle to allow aeration.")
        moist_score = 75
    else:
        moist_status = "Overwatered"
        moist_issues.append("Soil is waterlogged.")
        moist_recs.append("Disable irrigation. Improve soil drainage to prevent root rot.")
        moist_score = 40

    # 3. Environment Fallback
    env_issues = []
    env_recs = []
    env_score = 100
    risk_level = "Low"
    
    if temp < 15:
        env_issues.append("Cold Stress detected.")
        env_recs.append("Implement frost protection covers or thermal sheeting.")
        env_score -= 20
        risk_level = "Medium"
    elif temp > 35:
        env_issues.append("Heat Stress detected.")
        env_recs.append("Apply shading nets. Spray water during cooler hours to lower temperature.")
        env_score -= 20
        risk_level = "Medium"
        
    if humid < 30:
        env_issues.append("Dry Air Stress detected.")
        env_recs.append("Increase relative humidity using misting systems.")
        env_score -= 10
    elif humid > 80:
        env_issues.append("High disease risk from excessive humidity.")
        env_recs.append("Improve spacing and ventilation to mitigate fungal blight or powdery mildew.")
        env_score -= 20
        risk_level = "High" if risk_level != "Low" else "Medium"
        
    env_score = max(0, env_score)

    # 4. Advisor Consolidator Fallback
    overall_health = int((soil_score + moist_score + env_score) / 3)
    
    priority_actions = []
    issues_detected = soil_issues + moist_issues + env_issues
    
    if moist_status in ["Very Dry", "Overwatered"] or "High disease risk" in str(env_issues):
        if moist_status == "Very Dry":
            priority_actions.append("HIGH PRIORITY: Irrigate the field immediately to prevent wilt.")
        if moist_status == "Overwatered":
            priority_actions.append("HIGH PRIORITY: Turn off irrigation systems and inspect field drainage.")
        if humid > 80:
            priority_actions.append("HIGH PRIORITY: Implement fungal monitoring and improve ventilation.")
            
    for issue in soil_issues:
        priority_actions.append(f"MEDIUM PRIORITY: Remediation for {issue}")
        
    if not priority_actions:
        priority_actions.append("LOW PRIORITY: Routine maintenance and monitoring.")
        
    final_rec = (
        f"The {crop_name} crop shows an overall plant health score of {overall_health}%. "
        f"Key issues include: {', '.join(issues_detected) if issues_detected else 'None'}. "
        "Recommend maintaining current parameters or executing the priority actions listed below."
    )
    
    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "crop_name": crop_name,
        "inputs": {
            "nitrogen": n, "phosphorus": p, "potassium": k,
            "temperature": temp, "humidity": humid, "soil_moisture": moist
        },
        "soil": {
            "soil_score": soil_score,
            "issues": soil_issues,
            "recommendations": soil_recs
        },
        "moisture": {
            "moisture_score": moist_score,
            "moisture_status": moist_status,
            "issues": moist_issues,
            "recommendations": moist_recs
        },
        "environment": {
            "environment_score": env_score,
            "risk_level": risk_level,
            "issues": env_issues,
            "recommendations": env_recs
        },
        "advisor": {
            "overall_plant_health_score": overall_health,
            "overall_risk_level": risk_level,
            "priority_actions": priority_actions,
            "issues_detected": issues_detected,
            "final_recommendation": final_rec
        }
    }


def generate_pdf_report(data: dict) -> bytes:
    """Generates a PDF using fpdf2. Always generated in English to ensure safe font rendering."""
    try:
        from fpdf import FPDF
        
        class PlantPulsePDF(FPDF):
            def header(self):
                self.set_fill_color(27, 94, 32)
                self.rect(10, 10, 8, 8, 'F')
                self.set_font('helvetica', 'B', 14)
                self.set_text_color(27, 94, 32)
                self.cell(12)
                self.cell(0, 8, 'PlantPulse Guardian AI - Advisor Report', 0, 1, 'L')
                self.ln(4)
                
            def footer(self):
                self.set_y(-15)
                self.set_font('helvetica', 'I', 8)
                self.set_text_color(128, 128, 128)
                self.cell(0, 10, f'Page {self.page_no()}  |  Powered by Gemini & Google ADK', 0, 0, 'C')

        pdf = PlantPulsePDF()
        pdf.add_page()
        pdf.set_font('helvetica', '', 10)
        
        pdf.set_fill_color(240, 245, 241)
        pdf.rect(10, 22, 190, 30, 'F')
        pdf.set_xy(12, 24)
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 5, f"CROP DIAGNOSIS: {data['crop_name'].upper()}", 0, 1)
        pdf.set_font('helvetica', '', 9)
        pdf.cell(0, 4, f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", 0, 1)
        pdf.cell(0, 4, f"Metrics: N={data['inputs']['nitrogen']}, P={data['inputs']['phosphorus']}, K={data['inputs']['potassium']}, Temp={data['inputs']['temperature']}C, Humid={data['inputs']['humidity']}%, Moisture={data['inputs']['soil_moisture']}%", 0, 1)
        pdf.cell(0, 4, f"Health Score: {data['advisor']['overall_plant_health_score']}/100  |  Risk: {data['advisor']['overall_risk_level']}", 0, 1)
        pdf.ln(12)

        sections = [
            ("🌱 Soil Nutrition Details", data['soil'], 'soil_score'),
            ("💧 Soil Moisture Details", data['moisture'], 'moisture_score'),
            ("🌦 Environmental Details", data['environment'], 'environment_score')
        ]
        
        for name, sec_data, score_key in sections:
            pdf.set_font('helvetica', 'B', 11)
            pdf.set_text_color(27, 94, 32)
            pdf.cell(0, 6, name, 0, 1)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(2)
            
            pdf.set_font('helvetica', '', 9)
            pdf.set_text_color(50, 50, 50)
            pdf.cell(0, 4, f"Category Health Score: {sec_data[score_key]}/100", 0, 1)
            
            if 'moisture_status' in sec_data:
                pdf.cell(0, 4, f"Moisture Status: {sec_data['moisture_status']}", 0, 1)
            if 'risk_level' in sec_data:
                pdf.cell(0, 4, f"Risk Status: {sec_data['risk_level']}", 0, 1)
                
            issues = sec_data.get('issues', [])
            pdf.set_font('helvetica', 'B', 8)
            pdf.cell(0, 4, "Issues:", 0, 1)
            pdf.set_font('helvetica', '', 9)
            for issue in issues if issues else ["None"]:
                pdf.cell(5)
                pdf.cell(0, 4, f"- {issue}", 0, 1)
                
            recs = sec_data.get('recommendations', [])
            pdf.set_font('helvetica', 'B', 8)
            pdf.cell(0, 4, "Recommendations:", 0, 1)
            pdf.set_font('helvetica', '', 9)
            for rec in recs if recs else ["None"]:
                pdf.cell(5)
                pdf.cell(0, 4, f"- {rec}", 0, 1)
            pdf.ln(4)

        pdf.set_font('helvetica', 'B', 11)
        pdf.set_text_color(27, 94, 32)
        pdf.cell(0, 6, "🤖 Combined Advisor Recommendation", 0, 1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)
        
        pdf.set_font('helvetica', 'B', 8)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(0, 4, "Priority Directives:", 0, 1)
        pdf.set_font('helvetica', '', 9)
        for act in data['advisor'].get('priority_actions', []):
            pdf.cell(5)
            pdf.cell(0, 4, f"- {act}", 0, 1)
            
        pdf.ln(2)
        pdf.set_font('helvetica', 'B', 8)
        pdf.cell(0, 4, "Consolidated Summary:", 0, 1)
        pdf.set_font('helvetica', '', 9)
        pdf.multi_cell(0, 4, data['advisor'].get('final_recommendation', ''))
        
        return bytes(pdf.output())
    except Exception:
        report_str = f"PlantPulse Guardian AI - Advisor Report\n"
        report_str += f"Crop: {data['crop_name'].upper()}\n"
        report_str += f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_str += f"Overall Score: {data['advisor']['overall_plant_health_score']}/100\n"
        report_str += f"Overall Risk: {data['advisor']['overall_risk_level']}\n\n"
        report_str += "Final Recommendation Directive:\n"
        report_str += data['advisor'].get('final_recommendation', '')
        return report_str.encode('utf-8')


# ---------------------------------------------------------
# Sidebar Panel (Crop Selection & History)
# ---------------------------------------------------------
with st.sidebar:
    language = st.radio("Language / భాష", ["English", "Telugu"], horizontal=True)
    t = TRANSLATIONS[language]

    st.markdown("---")
    st.markdown(
        f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h2 style='color: #4caf50; margin-bottom: 5px;'>🌿 PlantPulse</h2>
            <span style='font-size: 0.9rem; color: var(--text-color); opacity: 0.8;'>{t['title']} Control Panel</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    crop_name = st.selectbox(
        t["crop_select"],
        ["Tomato", "Rice", "Maize", "Cotton", "Wheat", "Apple", "Banana", "Sugarcane", "Chilli", "Mango"]
    )
    
    st.markdown("---")
    st.markdown(f"### {t['history_title']}")
    
    if st.session_state.history:
        history_labels = [f"{idx+1}. {h['crop_name']} ({h['timestamp']})" for idx, h in enumerate(st.session_state.history)]
        selected_history = st.selectbox(t["reopen_report"], ["Select to view..."] + history_labels)
        
        if selected_history != "Select to view...":
            h_index = int(selected_history.split(".")[0]) - 1
            st.session_state.current_report = st.session_state.history[h_index]
            # Reload matching advice if present
            if "advice" in st.session_state.current_report:
                st.session_state.current_advice = st.session_state.current_report["advice"]
            st.info(f"Loaded report for {st.session_state.current_report['crop_name']}.")
    else:
        st.info(t["no_history"])


# ---------------------------------------------------------
# Main Panel Header & UI Components
# ---------------------------------------------------------
st.markdown(
    f"""
    <div class="main-container" style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
        <div style="
            background: linear-gradient(135deg, #1b5e20, #4caf50);
            width: 55px;
            height: 55px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.8rem;
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(76,175,80,0.25);
        ">
            🌿
        </div>
        <div>
            <h1 style="margin: 0px; color: var(--primary-color); font-size: 2.2rem; font-weight: 800;">{t['title']}</h1>
            <p style="margin: 0px; color: var(--text-color); font-size: 1rem; font-weight: 600; opacity: 0.85;">{t['subtitle']}</p>
            <p style="margin: 0px; color: var(--text-color); font-size: 0.8rem; opacity: 0.7;">{t['built_with']}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Render How It Works section
with st.expander(t["how_it_works_title"], expanded=False):
    st.markdown(
        f"""
        <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between; padding: 10px 0px; font-size: 0.9rem;">
            <div style="flex: 1; min-width: 200px; padding: 15px; background: rgba(128,128,128,0.05); border-radius: 8px; border-left: 4px solid #4caf50;">
                <p style="font-weight: 700; margin: 0px 0px 5px 0px; color: var(--primary-color);">{t['step_1']}</p>
                <p style="margin: 0px; opacity: 0.85;">{t['step_1_desc']}</p>
            </div>
            <div style="flex: 1; min-width: 200px; padding: 15px; background: rgba(128,128,128,0.05); border-radius: 8px; border-left: 4px solid #4caf50;">
                <p style="font-weight: 700; margin: 0px 0px 5px 0px; color: var(--primary-color);">{t['step_2']}</p>
                <p style="margin: 0px; opacity: 0.85;">{t['step_2_desc']}</p>
            </div>
            <div style="flex: 1; min-width: 200px; padding: 15px; background: rgba(128,128,128,0.05); border-radius: 8px; border-left: 4px solid #4caf50;">
                <p style="font-weight: 700; margin: 0px 0px 5px 0px; color: var(--primary-color);">{t['step_3']}</p>
                <p style="margin: 0px; opacity: 0.85;">{t['step_3_desc']}</p>
            </div>
            <div style="flex: 1; min-width: 200px; padding: 15px; background: rgba(128,128,128,0.05); border-radius: 8px; border-left: 4px solid #4caf50;">
                <p style="font-weight: 700; margin: 0px 0px 5px 0px; color: var(--primary-color);">{t['step_4']}</p>
                <p style="margin: 0px; opacity: 0.85;">{t['step_4_desc']}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

api_key = os.getenv("GEMINI_API_KEY")
if not api_key or api_key == "your_gemini_api_key_here":
    st.info(t["offline_notice"])
    use_fallback = True
else:
    use_fallback = False

# Set up parameter input forms
st.markdown(f"### {t['sensor_readings']}")
col_n, col_p, col_k = st.columns(3)
with col_n:
    n_val = st.slider(t["n_label"], min_value=0, max_value=100, value=45)
with col_p:
    p_val = st.slider(t["p_label"], min_value=0, max_value=100, value=25)
with col_k:
    k_val = st.slider(t["k_label"], min_value=0, max_value=100, value=35)

col_t, col_h, col_m = st.columns(3)
with col_t:
    t_val = st.slider(t["temp_label"], min_value=-10.0, max_value=50.0, value=28.0)
with col_h:
    h_val = st.slider(t["humid_label"], min_value=0, max_value=100, value=65)
with col_m:
    m_val = st.slider(t["moist_label"], min_value=0, max_value=100, value=45)

weather_input = st.text_input(
    t["weather_forecast_label"],
    value="Sunny days, no rain forecast for the next 3 days." if language == "English" else "ఎండగా ఉంది, రాబోయే 3 రోజుల్లో వర్షం కురిసే అవకాశం లేదు."
)

st.markdown(f"### {t['actions']}")
col_btn1, col_btn2, _ = st.columns([1.5, 1, 6])
analyze_clicked = False
with col_btn1:
    if st.button(t["analyze_btn"]):
        analyze_clicked = True
with col_btn2:
    if st.button(t["reset_btn"]):
        st.session_state.current_report = None
        st.session_state.current_advice = None
        st.rerun()


# ---------------------------------------------------------
# Execution / Processing Block
# ---------------------------------------------------------
if analyze_clicked:
    # Set up execution progress bar
    status_box = st.empty()
    prog_bar = st.progress(0)
    
    if use_fallback:
        status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>⚙️ {t['running_soil']}</p>", unsafe_allow_html=True)
        prog_bar.progress(30)
        time.sleep(0.4)
        status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>⚙️ {t['running_moisture']}</p>", unsafe_allow_html=True)
        prog_bar.progress(60)
        time.sleep(0.4)
        status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>⚙️ {t['running_env']}</p>", unsafe_allow_html=True)
        prog_bar.progress(85)
        time.sleep(0.4)
        
        report = local_rule_fallback(crop_name, n_val, p_val, k_val, t_val, h_val, m_val)
        advice = generate_static_farmer_advice(report, language)
        report["advice"] = advice
        
        prog_bar.progress(100)
        status_box.success(t["analysis_complete"])
        
        st.session_state.current_report = report
        st.session_state.current_advice = advice
    else:
        async def run_diagnostics():
            try:
                # 1. Soil Agent
                status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>🔬 {t['running_soil']}</p>", unsafe_allow_html=True)
                prog_bar.progress(15)
                soil_runner = InMemoryRunner(agent=soil_agent)
                soil_prompt = f"Analyze soil metrics. Do not call sensor tools: Nitrogen={n_val}, Phosphorus={p_val}, Potassium={k_val}."
                soil_resp = await soil_runner.run_debug(soil_prompt)
                soil_parsed = extract_output_from_events(soil_resp)
                
                # 2. Moisture Agent
                status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>💧 {t['running_moisture']}</p>", unsafe_allow_html=True)
                prog_bar.progress(45)
                moisture_runner = InMemoryRunner(agent=moisture_agent)
                moisture_prompt = f"Analyze soil moisture. Do not call sensor tools: Soil Moisture={m_val}%."
                moisture_resp = await moisture_runner.run_debug(moisture_prompt)
                moisture_parsed = extract_output_from_events(moisture_resp)
                
                # 3. Environment Agent
                status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>🌦 {t['running_env']}</p>", unsafe_allow_html=True)
                prog_bar.progress(70)
                env_runner = InMemoryRunner(agent=environment_agent)
                env_prompt = f"Analyze atmospheric conditions. Do not call sensor tools: Temperature={t_val}°C, Humidity={h_val}%. Forecast: {weather_input}."
                env_resp = await env_runner.run_debug(env_prompt)
                env_parsed = extract_output_from_events(env_resp)
                
                # 4. Advisor Agent
                status_box.markdown(f"<p style='font-size: 1.1rem; font-weight: 600; color: var(--primary-color);'>🤖 {t['running_advisor']}</p>", unsafe_allow_html=True)
                prog_bar.progress(90)
                advisor_runner = InMemoryRunner(agent=advisor_agent)
                advisor_input = {
                    "SoilAnalysis": soil_parsed,
                    "MoistureAnalysis": moisture_parsed,
                    "EnvironmentAnalysis": env_parsed
                }
                advisor_resp = await advisor_runner.run_debug(str(advisor_input))
                advisor_parsed = extract_output_from_events(advisor_resp)
                
                # Bundle base report
                report = {
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "crop_name": crop_name,
                    "inputs": {
                        "nitrogen": n_val, "phosphorus": p_val, "potassium": k_val,
                        "temperature": t_val, "humidity": h_val, "soil_moisture": m_val
                    },
                    "soil": soil_parsed,
                    "moisture": moisture_parsed,
                    "environment": env_parsed,
                    "advisor": advisor_parsed
                }
                
                # Generate Farmer Friendly advice via Gemini
                advice = get_ai_farmer_advice(report, language)
                report["advice"] = advice
                
                prog_bar.progress(100)
                status_box.success(t["analysis_complete"])
                
                st.session_state.current_report = report
                st.session_state.current_advice = advice
                
            except Exception as ex:
                prog_bar.empty()
                error_text = str(ex)
                if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
                    status_box.warning(
                        "⚠️ Daily Gemini AI quota has been reached.\n\n"
                        "Switching to Offline Expert Agriculture Mode..."
                    )

                elif "MALFORMED_FUNCTION_CALL" in error_text:
                    status_box.warning(
                        "⚠️ AI response formatting issue detected.\n\n"
                        "Switching to Offline Expert Agriculture Mode..."
                    )

                else:
                    status_box.warning(
                        "⚠️ AI service is temporarily unavailable.\n\n"
                        "Using Offline Expert Agriculture Mode."
                    )

    # Offline fallback
        fallback_report = local_rule_fallback(
            crop_name,
            n_val,
            p_val,
            k_val,
            t_val,
            h_val,
            m_val
        )

        fallback_advice = generate_static_farmer_advice(
            fallback_report,
            language
        )

        fallback_report["advice"] = fallback_advice

        st.session_state.current_report = fallback_report
        st.session_state.current_advice = fallback_advice
        # Run async diagnostics
        asyncio.run(run_diagnostics())


# ---------------------------------------------------------
# Dashboard Rendering Block (Bilingual Tabbed Design)
# ---------------------------------------------------------
report = st.session_state.current_report
advice = st.session_state.current_advice

if report and advice:
    st.markdown("---")
    st.markdown(f"## 📋 Diagnostic Dashboard - {report['crop_name']} Analysis ({report['timestamp']})")
    
    # Render Plant Health Score Circular Gauge & Risk Level Badges
    col_kpi1, col_kpi2 = st.columns(2)
    
    with col_kpi1:
        st.markdown(
            f"""
            <div class="metric-card" style="text-align: center; height: 100%;">
                <h4 style="margin: 0px 0px 15px 0px; color: var(--primary-color);">{t['health_score_title']}</h4>
            """,
            unsafe_allow_html=True
        )
        health_score = report["advisor"].get("overall_plant_health_score", 100)
        
        if health_score >= 80:
            gauge_color = "#2e7d32" 
            status_text = "Optimal" if language == "English" else "ఉత్తమం"
        elif health_score >= 50:
            gauge_color = "#ef6c00" 
            status_text = "Warning" if language == "English" else "హెచ్చరిక"
        else:
            gauge_color = "#c62828" 
            status_text = "Alert" if language == "English" else "ప్రమాదం"
            
        deg = int((health_score / 100) * 360)
        
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; align-items: center; padding: 10px 0px;">
                <div style="
                    position: relative;
                    width: 140px;
                    height: 140px;
                    border-radius: 50%;
                    background: conic-gradient({gauge_color} {deg}deg, rgba(128,128,128,0.2) 0deg);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.06);
                ">
                    <div style="
                        position: absolute;
                        width: 114px;
                        height: 114px;
                        border-radius: 50%;
                        background-color: var(--background-color, white);
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                    ">
                        <span style="font-size: 2.2rem; font-weight: 800; color: #4caf50;">{health_score}%</span>
                        <span style="font-size: 0.75rem; font-weight: 600; color: var(--text-color); text-transform: uppercase;">{status_text}</span>
                    </div>
                </div>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_kpi2:
        st.markdown(
            f"""
            <div class="metric-card" style="text-align: center; height: 100%;">
                <h4 style="margin: 0px 0px 30px 0px; color: var(--primary-color);">{t['risk_level_title']}</h4>
            """,
            unsafe_allow_html=True
        )
        risk = str(report["advisor"].get("overall_risk_level", "Low")).upper()
        
        if risk == "HIGH":
            badge_class = "badge-high"
            display_risk = t.get("High", "High")
        elif risk == "MEDIUM":
            badge_class = "badge-medium"
            display_risk = t.get("Medium", "Medium")
        else:
            badge_class = "badge-low"
            display_risk = t.get("Low", "Low")
            
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center; align-items: center; padding: 10px 0px;">
                <span class="badge {badge_class}">{display_risk.upper()}</span>
            </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Establish Tab Navigation
    tab_farmer, tab_tech = st.tabs([t["farmer_friendly_sec"], t["tech_report_sec"]])

    # ---------------------------------------------------------
    # TAB 1: Farmer-Friendly Advice Tab
    # ---------------------------------------------------------
    with tab_farmer:
        st.markdown(f"### 🧑‍🌾 {t['farmer_friendly_sec']}")
        
        # Display the 4 structured advice summary cards
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            st.markdown(
                f"""
                <div class="metric-card" style="height: 100%; border-left: 5px solid #c62828;">
                    <h4 style="margin-top:0px; color:#c62828;">🌱 {t['q_problem']}</h4>
                    <p style="font-size:0.95rem; margin-bottom:10px;"><b>{t['q_problem']}</b><br>{advice.get('problem', '')}</p>
                    <p style="font-size:0.9rem; opacity:0.85;"><b>{t['q_why']}</b><br>{advice.get('why', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_f2:
            st.markdown(
                f"""
                <div class="metric-card" style="height: 100%; border-left: 5px solid #1565c0;">
                    <h4 style="margin-top:0px; color:#1565c0;">📦 {t['q_fert']}</h4>
                    <p style="font-size:0.95rem;"><b>{t['q_fert']}</b><br>{advice.get('fertilizer', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_f3:
            st.markdown(
                f"""
                <div class="metric-card" style="height: 100%; border-left: 5px solid #2e7d32;">
                    <h4 style="margin-top:0px; color:#2e7d32;">💧 {t['q_do']}</h4>
                    <p style="font-size:0.95rem;"><b>{t['q_do']}</b><br>{advice.get('what_to_do', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        with col_f4:
            st.markdown(
                f"""
                <div class="metric-card" style="height: 100%; border-left: 5px solid #ef6c00;">
                    <h4 style="margin-top:0px; color:#ef6c00;">📅 {t['q_when']}</h4>
                    <p style="font-size:0.95rem; margin-bottom:10px;"><b>{t['q_when']}</b><br>{advice.get('when_to_apply', '')}</p>
                    <p style="font-size:0.9rem; color:#f44336;"><b>{t['q_prec']}</b><br>{advice.get('precautions', '')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
        # Display the crop-aware fertilizer cards with images
        recommended_ferts = get_recommended_fertilizers(report["crop_name"], report["soil"]["issues"])
        if recommended_ferts:
            st.markdown("---")
            st.markdown(f"### {t['fertilizer_rec_title']}")
            st.info(t["fertilizer_notice"])
            
            fert_cols = st.columns(len(recommended_ferts))
            for i, fert_name in enumerate(recommended_ferts):
                with fert_cols[i]:
                    fert_data = FERTILIZER_DB.get(fert_name)
                    if fert_data:
                        st.markdown(
                            f"""
                            <div class="metric-card" style="height: 100%;">
                                <h3 style="margin-top: 0px; color: var(--primary-color); border-bottom: 2px solid rgba(76,175,80,0.1); padding-bottom: 5px;">
                                    {fert_data['names'][language]}
                                </h3>
                            """,
                            unsafe_allow_html=True
                        )
                        st.image(fert_data["image"], use_container_width=True)
                        st.markdown(
                            f"""
                                <p style="font-size:0.9rem; margin-top:10px;"><b>Purpose:</b> {fert_data['purpose'][language]}</p>
                                <p style="font-size:0.9rem;"><b>Why Recommended:</b> {fert_data['why'][language]}</p>
                                <p style="font-size:0.9rem;"><b>Application Guide:</b> {fert_data['guidance'][language]}</p>
                                <p style="font-size:0.9rem;"><b>Best Time:</b> {fert_data['time'][language]}</p>
                                <p style="font-size:0.9rem; color:#f44336;"><b>Precautions:</b> {fert_data['precautions'][language]}</p>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

    # ---------------------------------------------------------
    # TAB 2: Technical AI Report Tab (Bilingual headers, English contents)
    # ---------------------------------------------------------
    with tab_tech:
        st.markdown(f"### 🔬 {t['tech_report_sec']}")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            # Soil Analysis Card
            soil_score = report["soil"].get("soil_score", 0)
            soil_issues = report["soil"].get("issues", [])
            soil_recs = report["soil"].get("recommendations", [])
            
            # Map issues and recommendations to selected language
            soil_issues_mapped = [translate_text(x, language) for x in soil_issues]
            soil_recs_mapped = [translate_text(x, language) for x in soil_recs]
            
            soil_issues_html = "".join([f"<li style='margin-bottom: 5px;'>⚠️ {x}</li>" for x in soil_issues_mapped]) if soil_issues_mapped else f"<li>✅ {t['optimal_health']}</li>"
            soil_recs_html = "".join([f"<li style='margin-bottom: 5px;'>🎯 {x}</li>" for x in soil_recs_mapped]) if soil_recs_mapped else f"<li>✅ {t['optimal_health']}</li>"
            
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>🌱 {t['soil_analysis'] if language == 'Telugu' else 'Soil Analysis'}</h3>
                    <p style="font-size:1.1rem; font-weight:700; color:#2e7d32; margin:10px 0px;">Score: {soil_score}/100</p>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Issues Detected:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{soil_issues_html}</ul>
                    </div>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Recommendations:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{soil_recs_html}</ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Environmental Analysis Card
            env_score = report["environment"].get("environment_score", 0)
            env_risk_raw = report["environment"].get("risk_level", "Low")
            env_risk = t.get(env_risk_raw, env_risk_raw)
            env_issues = report["environment"].get("issues", [])
            env_recs = report["environment"].get("recommendations", [])
            
            env_issues_mapped = [translate_text(x, language) for x in env_issues]
            env_recs_mapped = [translate_text(x, language) for x in env_recs]
            
            env_issues_html = "".join([f"<li style='margin-bottom: 5px;'>⚠️ {x}</li>" for x in env_issues_mapped]) if env_issues_mapped else f"<li>✅ {t['optimal_env']}</li>"
            env_recs_html = "".join([f"<li style='margin-bottom: 5px;'>🎯 {x}</li>" for x in env_recs_mapped]) if env_recs_mapped else f"<li>✅ {t['optimal_env']}</li>"
            
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>🌦 {t['environmental_analysis'] if language == 'Telugu' else 'Environmental Analysis'}</h3>
                    <p style="font-size:1.1rem; font-weight:700; color:#2e7d32; margin:10px 0px;">Score: {env_score}/100</p>
                    <p style="margin: 0px 0px 10px 0px; font-size: 0.95rem; font-weight: 600;">Risk Level: <span style="color:#2e7d32;">{env_risk}</span></p>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Issues Detected:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{env_issues_html}</ul>
                    </div>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Recommendations:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{env_recs_html}</ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col_t2:
            # Moisture Analysis Card
            moist_score = report["moisture"].get("moisture_score", 0)
            moist_status_raw = report["moisture"].get("moisture_status", "Optimal")
            moist_status = translate_text(moist_status_raw, language)
            moist_issues = report["moisture"].get("issues", [])
            moist_recs = report["moisture"].get("recommendations", [])
            
            moist_issues_mapped = [translate_text(x, language) for x in moist_issues]
            moist_recs_mapped = [translate_text(x, language) for x in moist_recs]
            
            moist_issues_html = "".join([f"<li style='margin-bottom: 5px;'>⚠️ {x}</li>" for x in moist_issues_mapped]) if moist_issues_mapped else f"<li>✅ {t['optimal_moisture']}</li>"
            moist_recs_html = "".join([f"<li style='margin-bottom: 5px;'>🎯 {x}</li>" for x in moist_recs_mapped]) if moist_recs_mapped else f"<li>✅ {t['optimal_moisture']}</li>"
            
            st.markdown(
                f"""
                <div class="metric-card">
                    <h3>💧 {t['moisture_analysis'] if language == 'Telugu' else 'Moisture Analysis'}</h3>
                    <p style="font-size:1.1rem; font-weight:700; color:#2e7d32; margin:10px 0px;">Score: {moist_score}/100</p>
                    <p style="margin: 0px 0px 10px 0px; font-size: 0.95rem; font-weight: 600;">Moisture Status: <span style="color:#2e7d32;">{moist_status}</span></p>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Issues Detected:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{moist_issues_html}</ul>
                    </div>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Recommendations:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{moist_recs_html}</ul>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Advisor Final Recommendation Card
            actions = report["advisor"].get("priority_actions", [])
            issues_det = report["advisor"].get("issues_detected", [])
            rec_summary = report["advisor"].get("final_recommendation", "")
            
            actions_mapped = [translate_text(x, language) for x in actions]
            issues_det_mapped = [translate_text(x, language) for x in issues_det]
            rec_summary_mapped = translate_text(rec_summary, language)
            
            actions_html = "".join([f"<li style='margin-bottom: 5px; font-weight:600; color:#4caf50;'>⚡ {x}</li>" for x in actions_mapped]) if actions_mapped else "<li>✅ No immediate priorities.</li>"
            issues_det_html = "".join([f"<li style='margin-bottom: 5px;'>⚠️ {x}</li>" for x in issues_det_mapped]) if issues_det_mapped else "<li>✅ No critical issues found.</li>"
            
            st.markdown(
                f"""
                <div class="metric-card" style="border: 1px solid rgba(76, 175, 80, 0.4);">
                    <h3>🤖 {t['ai_recommendation'] if language == 'Telugu' else 'AI Recommendation'}</h3>
                    <div style="margin-top:12px;">
                        <p style="font-weight:700; margin-bottom:5px; color:#4caf50;">Priority Action Items:</p>
                        <ul style="padding-left:20px; margin-top:0px; font-size:0.9rem;">{actions_html}</ul>
                    </div>
                    <div style="margin-top:12px;">
                        <p style="font-weight:600; margin-bottom:5px;">Issues Detected:</p>
                        <ul style="padding-left:20px; font-size:0.9rem; margin-top:0px; opacity:0.9;">{issues_det_html}</ul>
                    </div>
                    <div style="margin-top:15px; padding:12px; background:rgba(128,128,128,0.06); border-radius:8px; border-left:4px solid #4caf50;">
                        <p style="font-weight:600; margin:0px 0px 4px 0px;">Final Summary Report:</p>
                        <p style="margin:0px; font-size:0.9rem; line-height:1.4; opacity:0.95;">{rec_summary_mapped}</p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Downloads Panel
    st.markdown(f"### {t['download_title']}")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        # Download JSON
        json_str = json.dumps(report, indent=2)
        st.download_button(
            label=t["dl_json"],
            data=json_str,
            file_name=f"PlantPulse_Report_{report['crop_name']}_{time.strftime('%Y%m%d%H%M')}.json",
            mime="application/json"
        )
    with col_dl2:
        # Download PDF
        pdf_bytes = generate_pdf_report(report)
        st.download_button(
            label=t["dl_pdf"],
            data=pdf_bytes,
            file_name=f"PlantPulse_Report_{report['crop_name']}_{time.strftime('%Y%m%d%H%M')}.pdf",
            mime="application/pdf"
        )

# ---------------------------------------------------------
# Footer Section
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    f"""
    <div style="text-align: center; font-size: 0.9rem; opacity: 0.8; padding: 20px 0px;">
        <p>🌿 <b>{t['title']}</b> - {t['footer_text']}</p>
        <p style="font-size: 0.8rem; opacity: 0.7;">Powered by Google ADK | Gemini | Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
