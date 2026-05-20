import streamlit as st
import google.generativeai as genai

st.title("המנטור האישי שלי 🍏🏋️‍♂️")
st.write("ברוך הבא למערכת מעקב התזונה והאימונים שלך.")

user_input = st.text_input("מה אכלת או איזה אימון עשית עכשיו?")

if st.button("עדכן מערכת"):
    if user_input:
        with st.spinner("מנתח את הנתונים..."):
            try:
                # התחברות עם המפתח שלך
                genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                
                # הטריק: חיפוש אוטומטי של מודל תקין וזמין
                valid_model_name = None
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        valid_model_name = m.name
                        break
                
                if valid_model_name:
                    model = genai.GenerativeModel(valid_model_name)
                    
                    # הפנייה למוח
                    prompt = f"המשתמש הזין את המידע הבא: '{user_input}'. נתח אותו כיועץ תזונה וכושר. אם זה אוכל, הערך את הקלוריות והערכים התזונתיים המרכזיים. אם זו פעילות, הערך שריפת קלוריות. תן משוב קצר, מפרגן ופרקטי. תחזיר תשובה קצרה ובעברית."
                    
                    response = model.generate_content(prompt)
                    st.success("הנה הניתוח:")
                    st.write(response.text)
                else:
                    st.error("לא נמצא מודל זמין בחשבון הזה.")
                    
            except Exception as e:
                st.error(f"שגיאה מפורטת: {e}")
    else:
        st.warning("אנא הקלד משהו בתיבה לפני הלחיצה.")
