import streamlit as st
import uuid
from agent import compiled_graph

st.set_page_config(page_title="NotebookLM Lite", page_icon="📝", layout="centered")

# תמיכה מלאה בכתיבה מימין לשמאל (RTL) עבור עברית
st.markdown(
    """
    <style>
    .stApp {
        direction: RTL;
        text-align: right;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📝 NotebookLM בקטנה")
st.write("סוכן מחקר המשלב חיפוש אוטונומי באינטרנט עם אישור אנושי (Human-in-the-Loop) - מופעל ע\"י Groq")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "app_step" not in st.session_state:
    st.session_state.app_step = "INPUT"

config = {"configurable": {"thread_id": st.session_state.thread_id}}

with st.sidebar:
    st.subheader("ניהול מחקר")
    if st.button("🔄 התחל מחקר חדש"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.app_step = "INPUT"
        st.rerun()

# שלב א': הזנת נושא המחקר
if st.session_state.app_step == "INPUT":
    st.subheader("1. מה תרצי לחקור?")
    topic_input = st.text_input("הזן נושא או שאילתת מחקר:", placeholder="לדוגמה: השפעת בינה מלאכותית על עולם הרפואה")
    
    if st.button("התחל בחיפוש 🔍"):
        if not topic_input.strip():
            st.warning("אנא הזן נושא חוקי לחיפוש.")
        else:
            with st.spinner("הסוכן סורק את הרשת ומחפש מקורות..."):
                compiled_graph.invoke({"topic": topic_input}, config)
                st.session_state.app_step = "REVIEW"
                st.rerun()

# שלב ב': אישור המקורות על ידי המשתמש (Human in the Loop)
elif st.session_state.app_step == "REVIEW":
    state_snapshot = compiled_graph.get_state(config)
    raw_sources = state_snapshot.values.get("raw_sources", [])
    topic = state_snapshot.values.get("topic", "")
    
    st.subheader(f"🔍 מקורות שנמצאו עבור: {topic}")
    st.write("סמני ב-V רק את המקורות שאת רוצה לכלול בסיכום הסופי:")
    
    approved_sources = []
    
    for idx, source in enumerate(raw_sources):
        with st.container(border=True):
            is_approved = st.checkbox(
                f"**מקור {idx+1}: {source['title']}**", 
                value=True, 
                key=f"check_{idx}"
            )
            st.markdown(f"**קישור:** [{source['url']}]({source['url']})")
            st.write(source['content'])
            
            if is_approved:
                approved_sources.append(source)
                
    st.markdown("---")
    
    if st.button("אשר מקורות והפק סיכום סופי 🚀"):
        if not approved_sources:
            st.error("עליך לבחור לפחות מקור אחד כדי להמשיך.")
        else:
            with st.spinner("מייצר סיכום בעזרת Groq..."):
                compiled_graph.update_state(
                    config,
                    {"approved_sources": approved_sources},
                    as_node="process_approval"
                )
                compiled_graph.invoke(None, config)
                st.session_state.app_step = "SUMMARY"
                st.rerun()

# שלב ג': הצגת הסיכום
elif st.session_state.app_step == "SUMMARY":
    state_snapshot = compiled_graph.get_state(config)
    summary = state_snapshot.values.get("summary", "")
    approved_sources = state_snapshot.values.get("approved_sources", [])
    
    st.success("🎉 הסיכום מוכן!")
    st.markdown(summary)
    
    st.markdown("---")
    st.subheader("🔗 מקורות מידע ששימשו לסיכום זה:")
    for src in approved_sources:
        st.markdown(f"- [{src['title']}]({src['url']})")