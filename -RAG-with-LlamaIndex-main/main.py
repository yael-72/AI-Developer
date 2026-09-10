
import os
import ssl
import certifi
import urllib3
import requests


# אנחנו מחליפים את פונקציית ברירת המחדל של יצירת הקשר ב-SSL
# זה משפיע על כמעט כל ספרייה בפייתון, כולל Cohere ו-Pinecone
orig_create_default_context = ssl.create_default_context

def patched_create_default_context(*args, **kwargs):
    context = orig_create_default_context(*args, **kwargs)
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE  # ביטול מוחלט של האימות
    return context

ssl.create_default_context = patched_create_default_context
# -------------------------------------------

from pinecone import Pinecone
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.pinecone import PineconeVectorStore
from llama_index.embeddings.cohere import CohereEmbedding

# הגדרת נתיב לתעודה ליתר ביטחון (למרות שביטלנו אימות)
cert_path = os.path.join(os.getcwd(), "root_ca_x2_rsa.crt")
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['HTTpx_CA_BUNDLE'] = cert_path
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


from dotenv import load_dotenv

# טעינת המשתנים מקובץ ה-.env
load_dotenv()

# משיכת המפתחות לתוך משתנים
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
COHERE_API_KEY = os.getenv("COHERE_API_KEY") # אם את משתמשת בו

Settings.embed_model = CohereEmbedding(
    api_key=os.environ["COHERE_API_KEY"],
    model_name="embed-multilingual-v3.0"
)

def file_metadata_helper(file_path):
    tool_name = "Other"
    path_lower = file_path.lower()
    if "claude" in path_lower: tool_name = "Claude"
    elif "cursor" in path_lower: tool_name = "Cursor"
    return {"tool": tool_name, "file_name": os.path.basename(file_path)}

def run_ingestion():
    print("--- ☁️ מעלה נתונים ל-Pinecone (ניסיון עקיפה אגרסיבי) ---")
    try:
        reader = SimpleDirectoryReader(input_dir="./data_source", recursive=True, file_metadata=file_metadata_helper)
        documents = reader.load_data()
        
        # חיבור ל-Pinecone
        pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"], ssl_verify=False)
        pinecone_index = pc.Index("rag-index")
        vector_store = PineconeVectorStore(pinecone_index=pinecone_index)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        print(f"🔄 מעבד {len(documents)} קבצים ומייצר Embeddings...")
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, show_progress=True)
        
        print(f"--- ✅ הצלחה מוחלטת! המידע עלה. ---")
    except Exception as e:
        print(f"❌ שגיאה: {e}")

if __name__ == "__main__":
    run_ingestion()