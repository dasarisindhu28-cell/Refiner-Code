import gradio as gr
import os
import subprocess
from groq import Groq
from dotenv import load_dotenv

# =========================
# LOAD API KEY
# =========================
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# =========================
# LANGUAGE EXTENSIONS
# =========================
EXTENSIONS = {
    "Python": ".py",
    "C": ".c",
    "C++": ".cpp",
    "Java": ".java",
    "JavaScript": ".js"
}
languages = list(EXTENSIONS.keys())

# =========================
# SAFE LLM CALL
# =========================
def ask_llm(prompt):
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"❌ Connection error:\n{e}"

# =========================
# CORE FUNCTIONS
# =========================
def review_code(code, language):
    prompt = f"""
You are a senior software engineer.
Analyze this {language} code.

Rules:
• Keep explanation SHORT
• Bullet points only
• Max 5–6 points

Return EXACTLY:

Issues:
- ...

Fix Suggestions:
- ...

Formatted Code:
<only corrected code>

Code:
{code}
"""
    result = ask_llm(prompt)
    if "Formatted Code:" in result:
        review_text, formatted = result.split("Formatted Code:", 1)
    else:
        review_text = result
        formatted = ""
    return review_text.strip(), formatted.strip()

def convert_code(code, source, target):
    prompt = f"""
Convert this {source} code to {target}.
Keep the same logic.
Only output converted code.

Code:
{code}
"""
    return ask_llm(prompt)

def chat_fn(message, history):
    reply = ask_llm(message)
    history = history or []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": reply})
    return "", history

def load_file(file):
    if file is None:
        return ""
    return open(file.name, "r", encoding="utf-8").read()

def generate_filename(code, language, suffix):
    prompt = f"""
Suggest a **short, meaningful filename** (no spaces, lowercase) for this {language} code. 
Use only one word if possible. Respond with only the filename, no extension.

Code:
{code}
"""
    suggested_name = ask_llm(prompt).strip()
    if not suggested_name:
        suggested_name = "my_code"
    ext = EXTENSIONS.get(language, ".txt")
    return f"{suggested_name}_{suffix}{ext}"

def save_file(text, filename):
    name, ext = os.path.splitext(filename)
    if ext == "":
        ext = ".txt"
        filename = name + ext
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    try:
        subprocess.Popen(["code", filename])
    except:
        pass
    return filename

# =========================
# CUSTOM CSS
# =========================
custom_css = """
<style>
html, body, .gradio-container {
    height: 100%;
    background: linear-gradient(to right, #e0f7fa, #e1bee7);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
h1 { font-size:60px !important; font-weight:bold; text-align:center; margin-bottom:20px; }
h2 { text-align:center; font-weight:bold; margin-bottom:20px; }
.welcome-line { background-color:#ffe082; padding:25px; border-radius:20px; font-size:28px; text-align:center; font-weight:bold; margin-bottom:40px; }
.feature-card { background:white; padding:30px; border-radius:20px; box-shadow:0 6px 20px rgba(0,0,0,0.1); text-align:center; transition:0.3s; width:100%; max-width:300px; margin:auto; }
.feature-card:hover { transform:scale(1.05); }
.feature-card.selected { border:3px solid #6366f1; box-shadow:0 8px 25px rgba(0,0,0,0.2); transform:scale(1.08); transition:0.3s; }
.gr-button { background: linear-gradient(90deg,#6366f1,#4f46e5) !important; color:white !important; font-weight:bold !important; font-size:20px !important; border-radius:14px; margin-top:15px; width:100%; }
.filename-box { margin-top:10px; font-weight:bold; font-size:18px; }
@media (max-width:768px) {
    h1 { font-size:48px !important; }
    .welcome-line { font-size:22px; padding:20px; }
    .feature-card { max-width:90%; margin-bottom:20px; }
    .gr-row { flex-direction:column !important; }
}
</style>
"""

# =========================
# GRADIO UI
# =========================
with gr.Blocks(title="CodeRefine AI") as demo:
    gr.HTML(custom_css)
    
    # ===== HOME PAGE =====
    with gr.Column(visible=True) as home_page:
        gr.Markdown("<h1>🚀 CodeRefine AI</h1>")
        gr.Markdown('<div class="welcome-line">👋 Welcome! Choose a Feature</div>')
        
        with gr.Row():  # First row: Analysis + Converter
            with gr.Column(elem_classes="feature-card"):
                gr.Markdown("### 🔍 AI Code Analysis")
                analysis_card = gr.Button("Open")
            with gr.Column(elem_classes="feature-card"):
                gr.Markdown("### 🔄 Code Converter")
                converter_card = gr.Button("Open")
        with gr.Row():  # Second row: Chatbot
            with gr.Column(elem_classes="feature-card"):
                gr.Markdown("### 💬 AI Chatbot")
                chatbot_card = gr.Button("Open")

    # ===== ANALYSIS PAGE =====
    with gr.Column(visible=False) as analysis_page:
        gr.Markdown('<h2>🔍 AI Code Analysis</h2>')
        back1 = gr.Button("⬅ Back", elem_classes="gr-button")
        with gr.Column(elem_classes="feature-card"):
            file_upload = gr.File(label="Upload Code File")
            code_input = gr.Code(lines=20)
            file_upload.change(load_file, file_upload, code_input)
            lang = gr.Dropdown(languages, value="Python")
            review_btn = gr.Button("Run Analysis")
            review_output = gr.Textbox(label="AI Review", lines=10)
            formatted_output = gr.Code(label="Formatted Code", lines=15)
            filename_edit = gr.Textbox(label="Filename (editable)", placeholder="Enter filename here")
            download_btn = gr.File(label="Download File", interactive=True)

            def analyze_prepare(code, lang, user_filename):
                review_text, formatted = review_code(code, lang)
                if user_filename.strip():
                    filename = user_filename.strip()
                    if not any(filename.endswith(ext) for ext in EXTENSIONS.values()):
                        filename += EXTENSIONS.get(lang, ".txt")
                else:
                    filename = generate_filename(code, lang, "optimized")
                file_path = save_file(formatted, filename)
                return review_text, formatted, filename, file_path

            review_btn.click(
                analyze_prepare,
                [code_input, lang, filename_edit],
                [review_output, formatted_output, filename_edit, download_btn]
            )

    # ===== CONVERTER PAGE =====
    with gr.Column(visible=False) as converter_page:
        gr.Markdown('<h2>🔄 Code Converter</h2>')
        back2 = gr.Button("⬅ Back", elem_classes="gr-button")
        with gr.Column(elem_classes="feature-card"):
            upload2 = gr.File()
            code2 = gr.Code(lines=20)
            upload2.change(load_file, upload2, code2)
            src = gr.Dropdown(languages, value="Python")
            tgt = gr.Dropdown(languages, value="JavaScript")
            convert_btn2 = gr.Button("Convert Code")
            converted = gr.Code()
            filename_edit2 = gr.Textbox(label="Filename (editable)", placeholder="Enter filename here")
            download_btn2 = gr.File(label="Download File", interactive=True)

            def convert_prepare(code, src_lang, tgt_lang, user_filename):
                converted_code = convert_code(code, src_lang, tgt_lang)
                if user_filename.strip():
                    filename = user_filename.strip()
                    if not any(filename.endswith(ext) for ext in EXTENSIONS.values()):
                        filename += EXTENSIONS.get(tgt_lang, ".txt")
                else:
                    filename = generate_filename(code, tgt_lang, "converted")
                file_path = save_file(converted_code, filename)
                return converted_code, filename, file_path

            convert_btn2.click(
                convert_prepare,
                [code2, src, tgt, filename_edit2],
                [converted, filename_edit2, download_btn2]
            )

    # ===== CHATBOT PAGE =====
    with gr.Column(visible=False) as chatbot_page:
        gr.Markdown('<h2>💬 AI Coding Chatbot</h2>')
        back3 = gr.Button("⬅ Back", elem_classes="gr-button")
        with gr.Column(elem_classes="feature-card"):
            chatbot = gr.Chatbot(height=500)
            msg = gr.Textbox(placeholder="Ask coding doubts...")
            msg.submit(chat_fn, [msg, chatbot], [msg, chatbot])

    # ===== HELPER: CARD SELECTION =====
    def select_card(card_name):
        return [
            gr.update(elem_classes="feature-card" + (" selected" if card_name=="analysis" else "")),
            gr.update(elem_classes="feature-card" + (" selected" if card_name=="converter" else "")),
            gr.update(elem_classes="feature-card" + (" selected" if card_name=="chatbot" else ""))
        ]

    # ===== NAVIGATION =====
    analysis_card.click(
        lambda: (
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            *select_card("analysis")
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )
    converter_card.click(
        lambda: (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            *select_card("converter")
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )
    chatbot_card.click(
        lambda: (
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            *select_card("chatbot")
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )
    back1.click(
        lambda: (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            *select_card(None)
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )
    back2.click(
        lambda: (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            *select_card(None)
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )
    back3.click(
        lambda: (
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=False),
            *select_card(None)
        ),
        outputs=[home_page, analysis_page, converter_page, chatbot_page, analysis_card, converter_card, chatbot_card]
    )

demo.launch()
