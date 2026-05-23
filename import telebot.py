import streamlit as st
import google.generativeai as genai

# --- תצורה בסיסית של העמוד ---
st.set_page_config(page_title="המנטור האישי", page_icon="💪")
st.title("המנטור האישי שלי 🍏🏋️‍♂️")

# --- אתחול הזיכרון (Session State) ---
# זה מה שמאפשר לאתר לזכור את היסטוריית השיחה לאורך היום
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "בוקר טוב! המערכת מאופסת להיום. היעדים שלנו להיום: 2,200 קלוריות ו-150 גרם חלבון. איך מתחילים? אפשר לעדכן על אוכל, אימון, או סתם התייעצות לגבי הלוז."}
    ]
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# --- הגדרת פרופיל המשתמש וההתנהגות הנסתרת של הבוט ---
SYSTEM_BEHAVIOR = """
אתה מנטור תזונה וכושר שמלווה את המשתמש בממשק צ'אט. 

סגנון ותקשורת:
- דבר תמיד בגובה העיניים, בצורה טבעית, ישירה ולעניין.
- אל תהיה רובוטי בשום צורה. אל תשתמש בתבניות קבועות (כמו "התשובה הקצרה היא...").
- אל תחלק מחמאות ריקות. היה ממוקד נתונים ופתרונות.

נתוני בסיס של המשתמש:
- יעד קלוריות יומי: 2200. 
- יעד חלבון יומי: 150 גרם. 

חוקי המערכת ("גמישות רדיקלית" - חובה עליך ליישם):
1. אפס רגשות אשם: לעולם אל תעביר ביקורת, תשפוט, או תביע אכזבה אם המשתמש לא התאמן, אכל ג'אנק, או חרג מהיעדים.
2. חלונות זמן קצרים: אם המשתמש מדווח על חוסר זמן או עייפות, הצע לו אימון מינימלי בבית של 10-15 דקות (למשל: סקוואטים, שכיבות סמיכה) במקום אימון מלא.
3. תנועה יומיומית: אם המשתמש מדווח על פעילות יומיומית, למשל טיול ארוך עם הכלב (הוגו), החשב זאת כפעילות גופנית לגיטימית (התאוששות פעילה/אירובי) ושבח אותו על התנועה.
4. ניתוח בזמן אמת: בכל פעם שהמשתמש מזין אוכל, עשה הערכה של הקלוריות והחלבון, וציין בקצרה מה נשאר לו להמשך היום.
"""

# --- חיבור ל-API וטעינת הצ'אט ---
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    
    # חיפוש דינמי של המודל כדי למנוע שגיאות גרסה
    if st.session_state.chat_session is None:
        valid_model_name = None
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                valid_model_name = m.name
                break
        
        if valid_model_name:
            model = genai.GenerativeModel(valid_model_name)
            # פתיחת חלון שיחה שזוכר את ההקשר
            st.session_state.chat_session = model.start_chat(history=[])
            # שתילת ה"אופי" של הבוט בזיכרון השיחה בשקט, בלי שהמשתמש יראה
            st.session_state.chat_session.send_message(SYSTEM_BEHAVIOR + "\n\nזהו הבסיס שלך לפעולה. אל תציג למשתמש אישור על ההודעה הזו, רק תפעל לפיה מעתה והלאה.")
        else:
            st.error("לא נמצא מודל זמין לחיבור.")
except Exception as e:
    st.error(f"שגיאת התחברות ל-API. ודא שהמפתח ב-Secrets תקין. פרטים: {e}")

# --- תצוגת היסטוריית השיחה על המסך ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- קליטת הודעה חדשה מהמשתמש ---
# התיבה הזו תופיע באופן אוטומטי בתחתית המסך
if prompt := st.chat_input("מה אוכלים? התאמנת? או שסתם בא לך להתייעץ..."):
    # 1. הצגת הודעת המשתמש במסך
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # 2. שליחה למוח וקבלת תשובה
    with st.chat_message("assistant"):
        with st.spinner("מעבד נתונים..."):
            try:
                response = st.session_state.chat_session.send_message(prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"שגיאה בניתוח ההודעה: {e}")
