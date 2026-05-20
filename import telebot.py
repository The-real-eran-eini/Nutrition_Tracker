import streamlit as st
import google.generativeai as genai

# משיכת המפתח מתוך הכספת של סטרימליט
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

st.title("המנטור האישי שלי 🍏🏋️‍♂️")
st.write("ברוך הבא למערכת מעקב התזונה והאימונים שלך.")

user_input = st.text_input("מה אכלת או איזה אימון עשית עכשיו?")

if st.button("עדכן מערכת"):
    if user_input:
        with st.spinner("מנתח את הנתונים..."):
            try:
                # ההוראה שאני מקבל מאחורי הקלעים כדי לנתח את המשפט שלך
                prompt = f"המשתמש הזין את המידע הבא: '{user_input}'. נתח אותו כיועץ תזונה וכושר. אם זה אוכל, הערך את הקלוריות והערכים התזונתיים המרכזיים. אם זו פעילות, הערך שריפת קלוריות. תן משוב קצר, מפרגן ופרקטי. תחזיר תשובה קצרה ובעברית."
                
                response = model.generate_content(prompt)
                st.success("הנה הניתוח:")
                st.write(response.text)
            except Exception as e:
                st.error("הייתה בעיה להתחבר למוח. ודא שמפתח ה-API הוזן נכון בהגדרות של סטרימליט.")
    else:
        st.warning("אנא הקלד משהו בתיבה לפני הלחיצה.")
