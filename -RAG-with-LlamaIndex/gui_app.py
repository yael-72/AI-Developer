
import os
import ssl
import urllib3
import asyncio
import gradio as gr
from chatPro import RAGWorkflow 

ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

agent_executor = RAGWorkflow(timeout=60)

async def agent_predict(message, history):
    try:
        result = await agent_executor.run(query=message)
        answer = result.get('answer', 'שגיאת מערכת.')
        sources = result.get('sources', [])

        if sources:
            answer += f"\n\n---\n🛰️ מקורות: {', '.join(sources)}"

        return answer

    except Exception as e:
        return f"⚠️ שגיאת מערכת: {str(e)}"


# -------------------------
# 🎨 ULTRA 2026 DESIGN + SIMPLE CHAT BUTTONS
# -------------------------
ultra_modern_css = """

@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');

body, .gradio-container{
background:
radial-gradient(circle at 25% 20%, rgba(99,102,241,0.25), transparent 40%),
radial-gradient(circle at 80% 10%, rgba(168,85,247,0.25), transparent 40%),
linear-gradient(135deg,#020617,#030712);

font-family:'Plus Jakarta Sans',sans-serif;
color:#f8fafc;
}

/* HEADER */
#main-header h1{
font-size:3rem;
font-weight:800;
text-align:center;
background:linear-gradient(90deg,#22d3ee,#6366f1,#c084fc);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}

/* CHAT WINDOW */
.chatbot{
background:rgba(15,23,42,0.95) !important;
border-radius:20px;
border:1px solid rgba(255,255,255,0.08);
box-shadow:0 0 40px rgba(99,102,241,0.2);
direction: rtl;
text-align: right;
}

/* BOT MESSAGE */
.message.bot{
background:#1e293b !important;
color:#f1f5f9 !important;
border-radius:14px;
border:1px solid rgba(255,255,255,0.06);
direction: rtl;
text-align: right;
}

/* USER MESSAGE */
.message.user{
background:linear-gradient(135deg,#6366f1,#a855f7) !important;
color:#ffffff !important;
border-radius:14px;
box-shadow:0 6px 20px rgba(99,102,241,0.4);
direction: rtl;
text-align: right;
}

/* FORCE TEXT VISIBILITY */
.chatbot p,
.chatbot span,
.chatbot div,
.chatbot li,
.chatbot strong,
.chatbot em{
color:#f1f5f9 !important;
font-size:15px;
line-height:1.6;
direction: rtl;
text-align: right;
}

/* CODE BLOCKS */
.chatbot code{
background:#020617;
color:#22d3ee;
padding:4px 6px;
border-radius:6px;
direction:ltr;
text-align:left;
}

/* INPUT BOX */
textarea,
input,
[data-testid="textbox"]{
background:#020617 !important;
color:#ffffff !important;
border-radius:14px;
border:1px solid rgba(255,255,255,0.15);
font-size:16px;
padding:14px;
direction: rtl;
text-align: right;
}

/* PLACEHOLDER */
::placeholder{
color:#64748b !important;
}

/* SIMPLE CHAT BUTTONS (no gradient, clean like GPT) */
.chatbot button{
background:#6366f1;
border:none;
color:white;
font-weight:500;
border-radius:6px;
padding:6px 12px;
margin-left:5px;
font-size:13px;
cursor:pointer;
}

.chatbot button:hover{
background:#4f46e5;
}

/* STATUS */
.status{
color:#22d3ee;
font-weight:600;
}

/* FOOTER */
footer{
display:none !important;
}

"""

with gr.Blocks(title="SMART QUERY") as demo:

    with gr.Column(elem_id="main-header"):

        gr.HTML("<h1>What would you like to explore today?</h1>")

        gr.Markdown(
        "<p style='text-align:center;color:#94a3b8;'>Next-Gen Agentic Intelligence Platform | 2026</p>"
        )

    with gr.Row():

        with gr.Column(scale=1):

            reset_btn = gr.Button("🔄 RESET MEMORY")

            gr.HTML("<div class='status'>● AGENT ONLINE</div>")

        with gr.Column(scale=4):

           gr.ChatInterface(
           fn=agent_predict,
        )

    reset_btn.click(fn=lambda: agent_executor.memory.reset())


if __name__ == "__main__":
    demo.launch(css=ultra_modern_css)