

import os
import ssl
import urllib3
import asyncio
import json
import re
from typing import Any, List, Optional
from pydantic import BaseModel, Field

# --- 🚀 שלב 1: עקיפת SSL בטוחה ---
orig_create_default_context = ssl.create_default_context
def patched_create_default_context(*args, **kwargs):
    context = orig_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context
ssl.create_default_context = patched_create_default_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['PYTHONHTTPSVERIFY'] = '0'

# --- 📚 שלב 2: ייבוא ספריות ---
from pinecone import Pinecone
from llama_index.utils.workflow import draw_all_possible_flows
from llama_index.core import VectorStoreIndex, Settings
from llama_index.core.workflow import (
    Event,
    StartEvent,
    StopEvent,
    Workflow,
    step,
)
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.base.llms.types import ChatMessage, MessageRole
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.cohere import CohereEmbedding
from llama_index.llms.gemini import Gemini
import google.generativeai as genai


from dotenv import load_dotenv

# טעינת המשתנים מקובץ ה-.env
load_dotenv()

# משיכת המפתחות לתוך משתנים
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY") 

# --- 🚀 שלב 3: ה-Mock ל-Gemini ---
def mock_get_model(name, **kwargs):
    class MockModel:
        def __init__(self, name):
            self.name = name
            self.supported_generation_methods = ["generateContent", "countTokens"]
            self.output_token_limit = 8192
            self.input_token_limit = 30720
            self.description = "Mock model"
    return MockModel(name)
genai.get_model = mock_get_model



# ⚙️ הגדרות
Settings.embed_model = CohereEmbedding(api_key=COHERE_KEY, model_name="embed-multilingual-v3.0")
Settings.llm = Gemini(api_key=GEMINI_KEY, model_name="models/gemini-flash-latest", transport="rest")
Settings.llm._is_fedramped = True

# --- 📡 שלב 4: הגדרת אירועים ---
class RetrievalEvent(Event):
    nodes: List[Any]
    query: str

class ExtractionEvent(Event):
    nodes: List[Any]
    query: str

class ValidationErrorEvent(Event):
    error_message: str

# --- 🔄 שלב 5: ה-Workflow המעודכן ---
class RAGWorkflow(Workflow):
    memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

    @step
    async def validate_and_retrieve(self, ev: StartEvent) -> Optional[RetrievalEvent | ExtractionEvent | ValidationErrorEvent]:
        query = ev.get("query", "").strip()
        if len(query) < 3:
            return ValidationErrorEvent(error_message="השאלה קצרה מדי.")

        print(f"🔍 [Agent] בודק ב-Pinecone...")
        pc = Pinecone(api_key=PINECONE_KEY, ssl_verify=False)
        index = pc.Index("rag-index")
        vector_store = PineconeVectorStore(pinecone_index=index)
        nodes = VectorStoreIndex.from_vector_store(vector_store).as_retriever(similarity_top_k=3).retrieve(query)
        
        highest_score = nodes[0].score if nodes and nodes[0].score else 0
        context_keywords = ["הראשון", "הקודם", "זה", "עוד", "הסבר", "פרט"]
        is_follow_up = any(word in query.lower() for word in context_keywords)
        
        if (not nodes or highest_score < 0.45) and not is_follow_up:
            return ValidationErrorEvent(error_message="לא נמצא מידע רלוונטי מספיק.")

        if is_follow_up and highest_score < 0.45:
             print("🧠 [Agent] שאלת המשך - מסתמך על זיכרון.")
             return RetrievalEvent(nodes=nodes if nodes else [], query=query)

        # נתיב חילוץ (לפי מילות מפתח)
        extraction_keywords = ["שינויים", "טבלאות", "רשימה", "חילוץ"]
        if any(word in query.lower() for word in extraction_keywords):
            print("⚡ [Router] עובר למסלול Extraction.")
            return ExtractionEvent(nodes=nodes, query=query)
        
        return RetrievalEvent(nodes=nodes, query=query)

    @step
    async def extract_data(self, ev: ExtractionEvent) -> StopEvent:
        print(f"🪄 [Agent] מחלץ נתונים ומנסח תשובה ידידותית...")
        context = "\n".join([n.get_content() for n in ev.nodes])
        
        # פרומפט שמבקש מהמודל גם JSON וגם תשובה אנושית
        prompt = (
            f"התבסס על ההקשר הבא:\n{context}\n\n"
            f"משימה:\n"
            f"1. חלץ את רשימת השינויים כ-JSON.\n"
            f"2. נסח תשובה קצרה ומקצועית בעברית שמסכמת למשתמש מה השתנה.\n\n"
            f"החזר בפורמט הבא:\n"
            f"JSON_START\n[ה-JSON כאן]\nJSON_END\n"
            f"TEXT_START\n[התשובה בעברית כאן]\nTEXT_END"
        )
        
        response = str(Settings.llm.complete(prompt))
        
        # חילוץ הטקסט הידידותי למשתמש
        friendly_text = re.search(r"TEXT_START\n(.*?)\nTEXT_END", response, re.DOTALL)
        json_content = re.search(r"JSON_START\n(.*?)\nJSON_END", response, re.DOTALL)
        
        answer = friendly_text.group(1).strip() if friendly_text else "הנה השינויים שמצאתי בתיעוד:"
        memory_data = json_content.group(1).strip() if json_content else response
        
        # עדכון זיכרון (שומרים את ה-JSON בשביל הדיוק להמשך)
        self.memory.put(ChatMessage(role=MessageRole.USER, content=ev.query))
        self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=memory_data))
        
        return StopEvent(result={"answer": answer, "sources": ["Extraction Mode"]})

    @step
    async def synthesize(self, ev: RetrievalEvent) -> StopEvent:
        print(f"🧠 [Agent] מייצר תשובה עם זיכרון...")
        context = "\n".join([n.get_content() for n in ev.nodes])
        history_str = "\n".join([f"{m.role}: {m.content}" for m in self.memory.get()])
        
        prompt = (
            f"הקשר מהתיעוד:\n{context}\n\n"
            f"היסטוריית שיחה:\n{history_str}\n\n"
            f"שאלה נוכחית: {ev.query}\n"
            f"ענה בעברית מקצועית."
        )
        
        response = Settings.llm.complete(prompt)
        self.memory.put(ChatMessage(role=MessageRole.USER, content=ev.query))
        self.memory.put(ChatMessage(role=MessageRole.ASSISTANT, content=str(response)))
        
        sources = list(set([f"קובץ: {n.metadata.get('file_name', 'Unknown')}" for n in ev.nodes]))
        return StopEvent(result={"answer": str(response), "sources": sources})

    @step
    async def handle_validation_error(self, ev: ValidationErrorEvent) -> StopEvent:
        return StopEvent(result={"answer": ev.error_message, "sources": []})

# --- 💬 שלב 6: לולאת הצ'אט ---
async def run_pro_chat():
    workflow = RAGWorkflow(timeout=60)
    print("\n🚀 [Agent Mode] סוכן חכם מוכן (עם תצוגה נקייה)!")
    
    while True:
        try:
            question = input("\nשאלה: ")
            if not question or question.lower() == 'exit': break
            result = await workflow.run(query=question)
            print(f"\n💡 תשובה: {result['answer']}")
            if result['sources']:
                print(f"📌 מקורות: {', '.join(result['sources'])}")
        except Exception as e:
            print(f"\n❌ שגיאה: {e}")

if __name__ == "__main__":
    asyncio.run(run_pro_chat())