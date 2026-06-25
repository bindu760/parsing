import os
import streamlit as st
from dotenv import load_dotenv
from llama_parse import LlamaParse
from groq import Groq

load_dotenv()

# -----------------------------
# API KEYS
# -----------------------------
LLAMA_KEY = os.getenv("LLAMA_PARSE_KEY")
GROQ_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

MODEL = "llama-3.3-70b-versatile"


# -----------------------------
# LOGIN SYSTEM
# -----------------------------
USERNAME = "Bindu"
PASSWORD = "1234"


def login():
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == USERNAME and p == PASSWORD:
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Wrong credentials")


# -----------------------------
# SESSION INIT
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "pdf_store" not in st.session_state:
    st.session_state["pdf_store"] = {}

# ✅ CHAT HISTORY (ChatGPT style)
if "chats" not in st.session_state:
    st.session_state["chats"] = {}

if "current_chat" not in st.session_state:
    st.session_state["current_chat"] = "Chat 1"
    st.session_state["chats"]["Chat 1"] = []


# -----------------------------
# LOGIN GATE
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
def parse_pdf(pdf_path):
    parser = LlamaParse(
        api_key=LLAMA_KEY,
        result_type="markdown",
        auto_mode=True,
        verbose=False,
    )

    docs = parser.load_data(pdf_path)
    return "\n".join(d.text for d in docs)


# -----------------------------
# GROQ CHAT (MULTI-TURN)
# -----------------------------
def ask_groq(messages):
    res = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    return res.choices[0].message.content


# -----------------------------
# NEW CHAT FUNCTION
# -----------------------------
def new_chat():
    chat_id = f"Chat {len(st.session_state['chats']) + 1}"
    st.session_state["chats"][chat_id] = []
    st.session_state["current_chat"] = chat_id


# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("📌 Dashboard")

if st.sidebar.button("➕ New Chat"):
    new_chat()

if st.sidebar.button("Logout"):
    st.session_state["logged_in"] = False
    st.rerun()


# chat switch
st.sidebar.subheader("💬 Chats")
for chat in st.session_state["chats"].keys():
    if st.sidebar.button(chat):
        st.session_state["current_chat"] = chat


# PDF selector
st.sidebar.subheader("📚 PDFs")

selected_pdf = st.sidebar.radio(
    "Select PDF",
    ["GENERAL CHAT"] + list(st.session_state["pdf_store"].keys())
)


# show last messages
st.sidebar.subheader("🧠 Recent Chat")
for msg in st.session_state["chats"][st.session_state["current_chat"]][-10:]:
    st.sidebar.write(f"**{msg['role']}**: {msg['content'][:40]}...")


# -----------------------------
# MAIN UI
# -----------------------------
st.title("📄 ChatGPT Style AI (PDF + Multi Chat)")


# -----------------------------
# MULTIPLE PDF UPLOAD
# -----------------------------
uploaded_files = st.file_uploader(
    "Upload PDFs",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    for file in uploaded_files:
        path = os.path.join(UPLOAD_DIR, file.name)

        with open(path, "wb") as f:
            f.write(file.read())

        if file.name not in st.session_state["pdf_store"]:
            with st.spinner(f"Parsing {file.name}..."):
                st.session_state["pdf_store"][file.name] = parse_pdf(path)

        st.success(f"{file.name} ready!")


# -----------------------------
# SHOW CHAT (ChatGPT UI)
# -----------------------------
current_chat = st.session_state["current_chat"]

for msg in st.session_state["chats"][current_chat]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])


# -----------------------------
# CHAT INPUT
# -----------------------------
user_input = st.chat_input("Ask something...")

if user_input:

    # decide context
    if selected_pdf == "GENERAL CHAT":
        context = ""
    else:
        context = st.session_state["pdf_store"].get(selected_pdf, "")

    # add user msg
    st.session_state["chats"][current_chat].append(
        {"role": "user", "content": user_input}
    )

    # build messages for groq
    messages = [
        {
            "role": "system",
            "content": "Answer using context if provided. Otherwise answer normally."
        }
    ]

    if context:
        messages.append({"role": "system", "content": f"Context:\n{context}"})

    messages += st.session_state["chats"][current_chat]

    # get response
    response = ask_groq(messages)

    st.session_state["chats"][current_chat].append(
        {"role": "assistant", "content": response}
    )

    st.rerun()