import streamlit as st
import google.generativeai as genai
import gspread
from google.oauth2.service_account import Credentials
import json
import datetime
import re

# --- תצורה בסיסית של העמוד ---
st.set_page_config(page_title="המנטור האישי", page_icon="💪")
st.title("המנטור האישי שלי 🍏🏋️‍♂️")

# --- אתחול הזיכרון (Session State) ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "בוקר טוב! המערכת מחוברת למסד הנתונים. המטרה שלנו: ריקומפוזיציה (2300 קלוריות, 140 גרם חלבון). עדכן אותי בארוחות, אימונים או תחושות."}
    ]
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# --- הגדרת פרופיל המשתמש ---
SYSTEM_BEHAVIOR = """
אתה מנטור תזונה וכושר אישי המלווה את המשתמש בממשק צ'אט. 

נתוני המשתמש:
- גיל: 31, גובה: 175 ס"מ, משקל: 70 ק"ג.
- מטרות העל: ריקומפוזיציה (העלאת מסת שריר וחיטוב במקביל), כוח פנימי, יציבות, גמישות וחיוניות.
- יעד קלוריות יומי: 2300 קלוריות.
- יעד חלבון יומי: 140 גרם (2 גרם לכל ק"ג גוף).

סגנון ותקשורת:
- דבר תמיד בגובה העיניים, בצורה טבעית, ישירה ולעניין.
- אל תהיה רובוטי בשום צורה. אל תשתמש בתבניות קבועות.
- אל תחלק מחמאות ריקות. היה ממוקד נתונים ופתרונות.

חוקי המערכת:
1. אפס רגשות אשם: לעולם אל תעביר ביקורת על חריגה מיעדים או פספוס אימון.
2. חלונות זמן קצרים: אם המשתמש מדווח על חוסר זמן, הצע אימוני כוח פונקציונליים בבית (10-15 דקות).
3. תנועה יומיומית: החשב הליכות וטיולים (למשל עם הכלב) כפעילות לגיטימית לכל דבר.
4. כוח ויציבות: תן דגש על תרגילי ליבה, שיווי משקל וגמישות לבניית "כוח פנימי".
5. ניתוח בזמן אמת: בכל הזנת אוכל, הערך קלוריות וחלבון וציין יתרה להמשך היום.
"""

# --- חיבור ל-API וטעינת הצ'אט ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    if st.session_state.chat_session is None:
        valid_model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                valid_model_name = m.name
                break
        
        if valid_model_name:
            st.session_state.model = genai.GenerativeModel(valid_model_name)
            st.session_state.chat_session = st.session_state.model.start_chat(history=[])
            st.session_state.chat_session.send_message(SYSTEM_BEHAVIOR + "\n\nזהו הבסיס שלך לפעולה. אל תציג אישור על ההודעה הזו.")
        else:
            st.error("לא נמצא מודל זמין לחיבור.")
except Exception as e:
    st.error(f"שגיאת התחברות ל-API: {e}")

# --- תצוגת היסטוריית השיחה ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- קליטת הודעה חדשה ועיבוד ---
if prompt := st.chat_input("מה אוכלים? התאמנת? או שסתם בא לך להתייעץ..."):
    # תצוגה במסך
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("מנתח..."):
            try:
                # 1. יצירת התשובה למשתמש
                response = st.session_state.chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
                # 2. גיבוי שקט ל-Google Sheets
                try:
                    # התחברות לגיליון
                    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
                    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
                    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
                    gc = gspread.authorize(creds)
                    sh = gc.open("Nutrition_DB").sheet1
                    
                    # בקשה מהמוח לחלץ נתונים לפורמט מסודר (נסתר מהמשתמש)
                    extraction_prompt = f"""
                    המשתמש כתב עכשיו: '{prompt}'
                    אתה ענית לו: '{response.text}'
                    
                    המטרה שלך היא לחלץ נתונים עבור מסד הנתונים מתוך האינטראקציה הזו. 
                    תחזיר אך ורק מבנה JSON תקין עם המפתחות הבאים:
                    "balance": "סיכום תזונתי של הארוחה והיתרה (אם לא דווח אוכל, כתוב 'ללא אוכל')",
                    "activity": "איזה אימון או פעילות בוצעה (אם לא בוצעה, כתוב 'ללא')",
                    "exertion": מספר בין 1 ל-10 המייצג את רמת המאמץ (אם אין, שים 0),
                    "notes": "הערה למנטור - תובנה אנליטית שלך לגבי המשתמש, דפוסים שזיהית או דגשים להמשך"
                    """
                    
                    extraction = st.session_state.model.generate_content(extraction_prompt)
                    
                    # איתור ה-JSON בתוך התשובה ושמירה
                    json_match = re.search(r'\{.*\}', extraction.text, re.DOTALL)
                    if json_match:
                        data = json.loads(json_match.group(0))
                        now = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
                        
                        # כתיבת השורה לגיליון
                        sh.append_row([
                            now, 
                            data.get("balance", ""), 
                            data.get("activity", ""), 
                            data.get("exertion", ""), 
                            data.get("notes", "")
                        ])
                except Exception as db_error:
                    # שגיאות גיליון יודפסו בשקט בלי להרוס את הצ'אט
                    print(f"Database sync error: {db_error}")

            except Exception as e:
                st.error(f"שגיאה בניתוח: {e}")
