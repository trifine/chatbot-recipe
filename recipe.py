import os
import streamlit as st
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


# =============================
# APP TITLE
# =============================
st.title("🍳 Resep Bergizi dari Bahan Anda")


# =============================
# API KEY SETUP
# =============================
# Cek apakah API key sudah ada
if "GOOGLE_API_KEY" not in os.environ:
    # Jika belum, minta user buat masukin API key
    google_api_key = st.text_input("Google API Key", type="password")
    # User harus klik Start untuk save API key
    start_button = st.button("Start")
    if start_button:
        os.environ["GOOGLE_API_KEY"] = google_api_key
        st.rerun()
    # Jangan tampilkan chat dulu kalau belum pencet start
    st.stop()

# =============================
# INIT LLM CLIENT
# =============================
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# =============================
# INITIALIZE SESSION STATE
# =============================
if "raw_image_bytes" not in st.session_state:
    st.session_state["raw_image_bytes"] = None

if "mime" not in st.session_state:
    st.session_state["mime"] = None

if "messages_history" not in st.session_state:
    system_prompt = (
        "Anda adalah 'Chef Cerdas', seorang Asisten Rekomendasi Resep yang ceria. "
        "Tugas Anda: 1) Analisis gambar bahan makanan, 2) Berikan rekomendasi resep "
        "yang bisa dibuat dari bahan tersebut. Tulis ramah, singkat, 5-7 kalimat."
    )
    st.session_state["messages_history"] = [
        SystemMessage(content=system_prompt)
    ]

# =============================
# IMAGE UPLOAD SECTION
# =============================
if st.session_state["raw_image_bytes"] is None:
    st.info("Silakan unggah foto bahan-bahan yang ada di kulkas/dapur Anda!")
    uploaded_image = st.file_uploader("Upload Foto Bahan Makanan", type=["jpg", "jpeg", "png"])

    if uploaded_image:
        st.session_state["raw_image_bytes"] = uploaded_image.read()
        st.session_state["mime"] = uploaded_image.type or "image/jpeg"
        st.rerun()

    st.stop()

# =============================
# DISPLAY UPLOADED IMAGE
# =============================
st.subheader("📸 Bahan Anda:")
st.image(st.session_state["raw_image_bytes"], caption="Bahan yang diunggah", width=300)


# =============================
# SHOW CHAT HISTORY (except system)
# =============================
for message in st.session_state["messages_history"]:
    if isinstance(message, SystemMessage):
        continue

    role = "User" if isinstance(message, HumanMessage) else "AI"

    with st.chat_message(role):
        # Jika content berupa multimodal list
        if isinstance(message.content, list):
            for part in message.content:
                if "text" in part:
                    st.write(part["text"])
        else:
            st.markdown(message.content)

# =============================
# USER CHAT INPUT
# =============================
# Baca prompt terbaru dari user
prompt = st.chat_input("Apa permintaan resep Anda? (contoh: 'Saya mau masakan Indonesia yang cepat dibuat")
if not prompt:
    st.stop()
# Jika user ada prompt, tampilkan promptnya langsung
with st.chat_message("User"):
    st.markdown(prompt)

# =============================
# BUILD MULTIMODAL MESSAGE
# =============================
image_part = {
    "mime_type": st.session_state["mime"],
    "data": st.session_state["raw_image_bytes"],
}

text_part = {
    "text": prompt
}
user_message = HumanMessage(content=[image_part, text_part])
st.session_state["messages_history"].append(user_message)

# =============================
# CALL GEMINI
# =============================
response = llm.invoke(st.session_state["messages_history"])
st.session_state["messages_history"].append(response)

# =============================
# DISPLAY RESPONSE
# =============================
with st.chat_message("AI"):
    if isinstance(response.content, list):
        # Gemini multimodal output
        for part in response.content:
            if "text" in part:
                st.write(part["text"])
    else:
        st.write(response.content)
