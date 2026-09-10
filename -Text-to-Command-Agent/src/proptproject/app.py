import os

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from proptproject.evaluator import evaluate
from proptproject.prompts import PROMPTS
from proptproject.sandbox import run_in_sandbox

load_dotenv()


def natural_to_cli(instruction: str, prompt_version: str) -> tuple[str, str]:
    """מחזיר (פקודה, סיכום הערכה)."""
    if not instruction.strip():
        return "", ""

    system_prompt = PROMPTS[prompt_version]
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": instruction},
        ],
        temperature=0,
        max_tokens=150,
    )

    command = response.choices[0].message.content.strip()
    eval_result = evaluate(command)
    return command, eval_result.summary()


def sandbox_run(command: str) -> str:
    if not command.strip():
        return ""
    return run_in_sandbox(command)


def create_app() -> gr.Blocks:
    prompt_choices = list(PROMPTS.keys())

    with gr.Blocks(title="Natural Language → CLI") as demo:
        gr.Markdown("# 🖥️ Natural Language → CLI Command")
        gr.Markdown(
            "הכנס הוראה בשפה טבעית וקבל פקודת **Windows Command Prompt** מוכנה להרצה."
        )

        prompt_selector = gr.Radio(
            choices=prompt_choices,
            value=prompt_choices[-1],
            label="גרסת פרומפט",
        )

        # ── שורה 1: קלט ופלט ─────────────────────────────────
        with gr.Row():
            with gr.Column(scale=1):
                instruction_input = gr.Textbox(
                    label="הוראה בשפה טבעית",
                    placeholder='לדוגמה: "מה כתובת ה-IP של המחשב שלי"',
                    lines=4,
                )
                submit_btn = gr.Button("המר לפקודה ▶", variant="primary")

            with gr.Column(scale=1):
                cli_output = gr.Textbox(
                    label="פקודת CLI",
                    lines=2,
                    interactive=False,
                )
                eval_output = gr.Textbox(
                    label="הערכה אוטומטית (פורמט | תחביר | בטיחות)",
                    lines=4,
                    interactive=False,
                )

        # ── שורה 2: סנדבוקס ──────────────────────────────────
        gr.Markdown("### 🧪 אימות בסנדבוקס")
        gr.Markdown(
            "הרצה בטוחה — **רק פקודות קריאה בלבד** מורצות. "
            "פקודות מסוכנות/משנות-מצב חסומות אוטומטית."
        )
        with gr.Row():
            sandbox_btn = gr.Button("▶ הרץ בסנדבוקס", variant="secondary")
        sandbox_output = gr.Textbox(
            label="פלט סנדבוקס",
            lines=6,
            interactive=False,
        )

        # ── קישורי אירועים ───────────────────────────────────
        submit_btn.click(
            fn=natural_to_cli,
            inputs=[instruction_input, prompt_selector],
            outputs=[cli_output, eval_output],
        )
        instruction_input.submit(
            fn=natural_to_cli,
            inputs=[instruction_input, prompt_selector],
            outputs=[cli_output, eval_output],
        )
        sandbox_btn.click(
            fn=sandbox_run,
            inputs=cli_output,
            outputs=sandbox_output,
        )

    return demo
