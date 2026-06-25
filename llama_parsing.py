
import os
import json
import streamlit as st
from dotenv import load_dotenv
from llama_parse import LlamaParse
from groq import Groq

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="PDF Chat Assistant",
    page_icon="📄",
    layout="wide"
)

load_dotenv()

# -----------------------------
# API KEYS
# -----------------------------
LLAMA_KEY = os.getenv("LLAMA_PARSE_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

MODEL = "llama-3.3-70b-versatile"

# -----------------------------
# LOGIN
# -----------------------------
USERNAME = os.getenv("APP_USER", "Bindu")
PASSWORD = os.getenv("APP_PASS", "1234")


def login():
    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("❌ Invalid username or password")


# -----------------------------
# SESSION STATE
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "pdf_store" not in st.session_state:
    st.session_state["pdf_store"] = {}

if "chats" not in st.session_state:
    st.session_state["chats"] = {
        "Chat 1": []
    }

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = "Chat 1"


# -----------------------------
# LOGIN CHECK
# -----------------------------
if not st.session_state["logged_in"]:
    login()
    st.stop()


# -----------------------------
# FOLDERS
# -----------------------------
UPLOAD_DIR = "pdfs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# -----------------------------
# PDF PARSER
# -----------------------------
@st.cache_data(show_spinner=False)
def parse_pdf(pdf_path):
    try:
        parser = LlamaParse(
            api_key=LLAMA_KEY,
            result_type="markdown",
            auto_mode=True,
            verbose=False,
        )

        docs = parser.load_data(pdf_path)

        return "\n".join(
            doc.text for doc in docs
        )

    except Exception as e:
        return f"Parsing Error: {e}"


# -----------------------------
# GROQ
# -----------------------------
def ask_groq(messages):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"Error: {e}"


# -----------------------------
# NEW CHAT
# -----------------------------
def new_chat():
    chat_id = f"Chat {len(st.session_state['chats']) + 1}"

    st.session_state["chats"][chat_id] = []
    st.session_state["current_chat"] = chat_id


# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:

    st.title("📌 Dashboard")

    if st.button("➕ New Chat"):
        new_chat()
        st.rerun()

    if st.button("🚪 Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    st.divider()

    # -------------------------
    # PDF UPLOAD
    # -------------------------
    st.subheader("📚 Upload PDFs")

    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:

        for file in uploaded_files:

            path = os.path.join(
                UPLOAD_DIR,
                file.name
            )

            with open(path, "wb") as f:
                f.write(file.read())

            if file.name not in st.session_state["pdf_store"]:

                with st.spinner(
                    f"Parsing {file.name}..."
                ):

                    parsed_text = parse_pdf(path)

                    st.session_state["pdf_store"][
                        file.name
                    ] = parsed_text

            st.success(f"✅ {file.name}")

    st.divider()

    # -------------------------
    # PDF SELECT
    # -------------------------
    st.subheader("📖 PDF Context")

    selected_pdf = st.radio(
        "Select Source",
        ["GENERAL CHAT"] +
        list(st.session_state["pdf_store"].keys())
    )

    # -------------------------
    # VIEW + DOWNLOAD PARSED PDF
    # -------------------------
    if selected_pdf != "GENERAL CHAT":

        st.download_button(
            label="📄 Download Parsed Markdown",
            data=st.session_state["pdf_store"][selected_pdf],
            file_name=f"{selected_pdf}.md",
            mime="text/markdown"
        )

    st.divider()

    # -------------------------
    # CHAT HISTORY
    # -------------------------
    st.subheader("💬 Chat History")

    for chat_name in st.session_state["chats"]:

        if st.button(
            chat_name,
            key=f"chat_{chat_name}"
        ):
            st.session_state["current_chat"] = chat_name
            st.rerun()

    st.divider()

    current_chat = st.session_state["current_chat"]

    # -------------------------
    # CLEAR CHAT
    # -------------------------
    if st.button("🗑 Clear Current Chat"):

        st.session_state["chats"][
            current_chat
        ] = []

        st.rerun()

    # -------------------------
    # DOWNLOAD JSON CHAT
    # -------------------------
    chat_json = json.dumps(
        st.session_state["chats"][current_chat],
        indent=4,
        ensure_ascii=False
    )

    st.download_button(
        label="⬇ Download Chat",
        data=chat_json,
        file_name=f"{current_chat}.json",
        mime="application/json"
    )

    # -------------------------
    # DOWNLOAD MARKDOWN CHAT
    # -------------------------
    chat_md = f"# {current_chat}\n\n"

    for msg in st.session_state["chats"][current_chat]:

        if msg["role"] == "user":
            chat_md += (
                f"## 👤 User\n\n"
                f"{msg['content']}\n\n"
            )
        else:
            chat_md += (
                f"## 🤖 Assistant\n\n"
                f"{msg['content']}\n\n"
            )

    st.download_button(
        label="📝 Download Markdown Chat",
        data=chat_md,
        file_name=f"{current_chat}.md",
        mime="text/markdown"
    )

    st.divider()

    # -------------------------
    # RECENT MESSAGES
    # -------------------------
    st.subheader("🧠 Recent Messages")

    recent = st.session_state["chats"][
        current_chat
    ][-5:]

    if recent:

        for msg in recent:

            st.write(
                f"**{msg['role']}**: "
                f"{msg['content'][:50]}..."
            )

    else:
        st.caption("No messages yet")


# -----------------------------
# MAIN PAGE
# -----------------------------
st.title("📄 Multi PDF Chat Assistant")

current_chat = st.session_state["current_chat"]

if selected_pdf == "GENERAL CHAT":
    st.info("🤖 General AI Chat Mode")
else:
    st.success(
        f"📚 Using PDF: {selected_pdf}"
    )
    if selected_pdf != "GENERAL CHAT":

        with st.expander(
        "📄 View Parsed Markdown"
    ):

            st.markdown(
            st.session_state["pdf_store"][
                selected_pdf
            ]
        )

# -----------------------------
# SHOW CHAT
# -----------------------------
for message in st.session_state["chats"][current_chat]:

    with st.chat_message(
        message["role"]
    ):
        st.markdown(
            message["content"]
        )

# -----------------------------
# USER INPUT
# -----------------------------
prompt = st.chat_input(
    "Ask anything..."
)

if prompt:

    # -------------------------
    # USER MESSAGE
    # -------------------------
    st.session_state["chats"][
        current_chat
    ].append(
        {
            "role": "user",
            "content": prompt
        }
    )

    # -------------------------
    # CONTEXT
    # -------------------------
    context = ""

    if selected_pdf != "GENERAL CHAT":

        context = st.session_state[
            "pdf_store"
        ].get(
            selected_pdf,
            ""
        )

        # Prevent token overflow
        context = context[:12000]

    # -------------------------
    # BUILD MESSAGES
    # -------------------------
    messages = [
        {
            "role": "system",
            "content": """
You are a helpful AI assistant.

If PDF context is provided,
answer from the PDF.

If answer is not found,
say:
'Information not found in PDF.'

If no PDF is selected,
answer normally.
"""
        }
    ]

    if context:

        messages.append(
            {
                "role": "system",
                "content":
                f"PDF Context:\n{context}"
            }
        )

    messages.extend(
        st.session_state["chats"][
            current_chat
        ]
    )

    # -------------------------
    # AI RESPONSE
    # -------------------------
    with st.spinner(
        "Thinking..."
    ):

        answer = ask_groq(
            messages
        )

    st.session_state["chats"][
        current_chat
    ].append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    st.rerun()