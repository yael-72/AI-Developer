# 📊 RAG with LlamaIndex | Multi-Agent Dev-Insights Platform
### "Who's actually making the decisions here?"

![LlamaIndex](https://img.shields.io/badge/Framework-LlamaIndex-blueviolet?style=for-the-badge)
![Pinecone](https://img.shields.io/badge/VectorDB-Pinecone-green?style=for-the-badge)
![Event-Driven](https://img.shields.io/badge/Architecture-Event--Driven-gold?style=for-the-badge)
![Status](https://img.shields.io/badge/Release-2026_Stable-blue?style=for-the-badge)

## 📌 סקירת הפרויקט
בעידן של **Agentic Coding**, כלי פיתוח כמו **Cursor**, **Claude Code** ו-**Kiro** יוצרים תיעוד אינסופי בקבצי `.md`. הבעיה? המידע מפוזר, סותר לעיתים, וקשה למעקב אנושי. 

**NEXUS AI** הוא יישום RAG מתקדם המאחד את כל שכבות הידע של כלי ה-AI השונים לתוך "שכבת אמת" (Single Source of Truth) אחת. המערכת מאפשרת למתכנתים לשלוט בתהליך, להבין החלטות טכניות ולעקוב אחרי שינויי ארכיטקטורה שבוצעו על ידי ה-AI.



## 🧠 יכולות ה-Agent (דוגמאות לתשאול)
המערכת יודעת להבדיל בין **חיפוש סמנטי** (הבנת הקשר) לבין **חילוץ נתונים מובנה** (שאלות קשיחות):

* **החלטות ארכיטקטוניות:** *"מה הצבע העיקרי שנבחר לדיזיין של המערכת?"* או *"מה הוחלט לגבי מבנה ה-DB?"*
* **חוקים ומגבלות:** *"האם קיימת הנחיה עקבית לגבי שימוש ב-RTL בממשק?"*
* **זיהוי רגישויות:** *"איזה רכיב במערכת הוגדר כבעייתי או רגיש במיוחד בתיעוד של Claude?"*
* **שאלות מבוססות זמן:** *"אילו שדות נוספו לטבלאות בשבוע האחרון?"*

## 🛠️ ארכיטקטורה וסטאק טכנולוגי
הפרויקט נבנה בארכיטקטורת **Event-Driven Workflow** מורכבת:

* **LlamaIndex & LlamaAgents:** ניהול תהליכים מרובי שלבים (Steps) מבוססי אירועים.
* **Cohere Embeddings:** יצירת ייצוג וקטורי איכותי למידע טכני.
* **Pinecone Vector Store:** אחזור סמנטי מהיר עם שימוש ב-Metadata לסינון לפי סוג כלי (Cursor/Claude).
* **Structured Data Extraction:** מנוע ייחודי המחלץ אובייקטים (JSON) של החלטות וכללים מתוך הטקסט הגולמי.
* **Smart Router:** רכיב החלטה המנתב את השאלה למסלול האופטימלי (Vector Search vs. Structured Query).

## 🧩 שלבי הפיתוח (Roadmap)
1.  **שלב א' (MVP):** בניית Pipeline בסיסי של Loading -> Chunking -> Embedding -> Retrieval.
2.  **שלב ב' (Event-Driven):** שכתוב המערכת ל-Workflow מבוסס אירועים (Events) המאפשר ולידציות וניתובים מורכבים.
3.  **שלב ג' (Extraction):** הוספת שכבת נתונים מובנית מעל קבצי ה-MD למענה על שאלות רשימתיות ומבוססות זמן.

## 🚀 הוראות הרצה

1.  **התקנת סביבה:**
    ```bash
    pip install llama-index cohere pinecone-client gradio
    ```
2.  **הגדרת מפתחות:**
    הגדר API Keys עבור Cohere, Pinecone ו-Gemini בתוך קובץ ה-`.env` שלך.
3.  **טעינת קבצים:**
    הנח את קבצי ה-`.md` של ה-Cursor/Claude שלך בתיקיות המקור.
4.  **הרצת הממשק:**
    ```bash
    python gui_app.py
    ```

## 📊 תרשים זרימה (Workflow)
המערכת מבוססת על Workflow שבו כל צעד משגר אירוע לצעד הבא. 
*(ניתן לצפות בתרשים הזרימה המלא בקובץ `workflow_graph.html` המצורף בריפו).*


