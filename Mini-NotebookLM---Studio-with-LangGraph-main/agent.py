import os
import json  # נוסף כדי לפענח את תוצאות החיפוש
from typing import List, Dict, Any
from typing_extensions import TypedDict
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_community.tools import TavilySearchResults
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

# Load keys from .env file
load_dotenv()

# 1. Define the State
class ResearchState(TypedDict):
    topic: str
    raw_sources: List[Dict[str, Any]]
    approved_sources: List[Dict[str, Any]]
    summary: str

# 2. Initialize Groq LLM (Llama 3.3) and Tavily Search
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)
tavily_tool = TavilySearchResults(max_results=5)

# 3. Define the Nodes
def search_node(state: ResearchState) -> Dict[str, Any]:
    topic = state.get("topic")
    if not topic:
        return {"raw_sources": []}
    
    # Execute search
    search_results = tavily_tool.invoke({"query": topic})
    
    # תיקון קריטי: אם התוצאה חזרה כמחרוזת טקסט (JSON), נהפוך אותה לרשימת מילונים
    if isinstance(search_results, str):
        try:
            search_results = json.loads(search_results)
        except Exception:
            # במקרה שהטקסט לא בפורמט JSON, נכניס אותו כמקור יחיד
            search_results = [{"title": "Search Result", "url": "", "content": search_results}]
            
    raw_sources = []
    for idx, result in enumerate(search_results):
        # וידוא שכל מקור הוא אכן מילון (dict)
        if isinstance(result, dict):
            raw_sources.append({
                "id": idx,
                "title": result.get("title", f"Source {idx + 1}"),
                "url": result.get("url", ""),
                "content": result.get("content", result.get("snippet", ""))
            })
        else:
            raw_sources.append({
                "id": idx,
                "title": f"Source {idx + 1}",
                "url": "",
                "content": str(result)
            })
            
    return {"raw_sources": raw_sources}

def process_approval_node(state: ResearchState) -> Dict[str, Any]:
    approved = state.get("approved_sources")
    if approved is None:
        return {"approved_sources": state.get("raw_sources", [])}
    return {}

def summarize_node(state: ResearchState) -> Dict[str, Any]:
    approved = state.get("approved_sources", [])
    topic = state.get("topic", "")
    
    if not approved:
        return {"summary": "No approved sources found to generate a summary."}
    
    # Format the context from approved sources
    context_list = []
    for src in approved:
        context_list.append(f"Title: {src['title']}\nURL: {src['url']}\nContent: {src['content']}\n---")
    context = "\n".join(context_list)
    
    # English prompt instructing the LLM to output Hebrew
    prompt = f"""
    You are an expert research assistant. Your task is to write a comprehensive, well-structured, and highly professional summary on the topic: "{topic}".
    
    Strict Guidelines:
    1. Base your summary ONLY on the approved sources provided below. Do not assume or extrapolate facts not mentioned in these sources.
    2. Format the output beautifully using Markdown (headers, bullet points, and bold text).
    3. Ensure a clear flow: introduction, main research points, and a concluding synthesis.
    4. Write the final summary in Hebrew.
    
    Approved Sources:
    {context}
    
    Generate the professional Hebrew summary now:
    """
    
    response = llm.invoke(prompt)
    return {"summary": str(response.content)}

# 4. Build the Graph Workflow
workflow = StateGraph(ResearchState)

workflow.add_node("search", search_node)
workflow.add_node("process_approval", process_approval_node)
workflow.add_node("summarize", summarize_node)

workflow.add_edge(START, "search")
workflow.add_edge("search", "process_approval")
workflow.add_edge("process_approval", "summarize")
workflow.add_edge("summarize", END)

memory = MemorySaver()

# Compile the graph with an interrupt before the approval step
compiled_graph = workflow.compile(
    checkpointer=memory,
    interrupt_before=["process_approval"]
)