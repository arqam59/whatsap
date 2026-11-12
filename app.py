from datetime import datetime
import uuid
import streamlit as st

# --- Constants & Configuration ---
MAX_MESSAGES = 500
AVATARS = ["😀", "😎", "🤖", "👽", "🐱", "🐼", "🦊", "🐸", "🔥", "⭐"]

st.set_page_config(page_title="GlassChat", page_width=440, layout="centered")

# --- Initialize Session State ---
if "client_id" not in st.session_state:
    st.session_state.client_id = uuid.uuid4().hex

if "users" not in st.session_state:
    st.session_state.users = {}

if "messages" not in st.session_state:
    st.session_state.messages = []

if "audio_store" not in st.session_state:
    st.session_state.audio_store = {}


# --- Helper Functions ---
def get_or_create_user():
    sid = st.session_state.client_id
    if sid not in st.session_state.users:
        is_first = len(st.session_state.users) == 0
        st.session_state.users[sid] = {
            "username": f"Guest-{len(st.session_state.users) + 1}",
            "avatar": "😀",
            "role": "host" if is_first else "user",
        }
    return st.session_state.users[sid]


def valid_display_name(value):
    return isinstance(value, str) and 1 <= len(value.strip()) <= 24


def append_message(message):
    st.session_state.messages.append(message)
    if len(st.session_state.messages) > MAX_MESSAGES:
        st.session_state.messages.pop(0)


# Get current user details
user = get_or_create_user()

# --- Custom CSS for Styling UI ---
st.markdown(
    """
<style>
.stApp {
    background: radial-gradient(circle at 15% 10%, #19365d 0, transparent 35%),
                radial-gradient(circle at 90% 90%, #321c58 0, transparent 38%), #08111f;
    color: #eef5ff;
}
.chat-bubble {
    padding: 10px 12px;
    border-radius: 17px;
    background: #ffffff10;
    border: 1px solid rgba(255,255,255,.14);
    margin-bottom: 8px;
}
.meta {
    font-size: 10px;
    color: #b8c5d8;
    margin-top: 4px;
}
</style>
""",
    unsafe_allow_html=True,
)

# --- Header Section ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown(f"### 💬 GlassChat")
    st.caption(f"Chatting as **{user['username']}**")
with col2:
    if st.button("Logout", key="logout_btn"):
        # Reset session identifier to log out / re-register user
        st.session_state.client_id = uuid.uuid4().hex
        st.rerun()

st.divider()

# --- Navigation Tabs ---
tab_chat, tab_profile = st.tabs(["💬 Chat Room", "👤 Profile"])

# ==========================================
# TAB 1: CHAT ROOM
# ==========================================
with tab_chat:
    # Message container with scroll simulation
    messages_container = st.container(height=400)
    with messages_container:
        if not st.session_state.messages:
            st.info("No messages yet. Start the conversation below!")
        for m in st.session_state.messages:
            is_mine = m["username"] == user["username"]
            align = "right" if is_mine else "left"

            with st.chat_message(
                "user" if is_mine else "assistant", avatar=m.get("avatar", "🙂")
            ):
                st.markdown(f"**{m['username']}**")
                if m.get("text"):
                    st.write(m["text"])
                if m.get("audio_id") and m["audio_id"] in st.session_state.audio_store:
                    audio_info = st.session_state.audio_store[m["audio_id"]]
                    st.audio(audio_info["data"], format=audio_info["mime"])
                st.markdown(
                    f"<div class='meta'>{m['time']}</div>", unsafe_allow_html=True
                )

    # Composer Form
    with st.form("chat_form", clear_on_submit=True):
        cols = st.columns([5, 1])
        with cols[0]:
            text_input = st.text_input(
                "Message", placeholder="Type a message…", label_visibility="collapsed"
            )
        with cols[1]:
            submitted = st.form_submit_button("Send", use_container_width=True)

        if submitted and text_input.strip():
            append_message(
                {
                    "id": str(uuid.uuid4()),
                    "username": user["username"],
                    "avatar": user["avatar"],
                    "text": text_input.strip()[:1000],
                    "audio_id": None,
                    "time": datetime.now().strftime("%H:%M"),
                }
            )
            st.rerun()

    # Audio recorder component (built into Streamlit natively)
    audio_val = st.audio_input("Record a voice note")
    if audio_val:
        audio_bytes = audio_val.read()
        if len(audio_bytes) > 2 * 1024 * 1024:
            st.error("Voice note too large (2 MB max).")
        else:
            audio_id = str(uuid.uuid4())
            st.session_state.audio_store[audio_id] = {
                "data": audio_bytes,
                "mime": "audio/wav",
                "owner": user["username"],
            }
            append_message(
                {
                    "id": str(uuid.uuid4()),
                    "username": user["username"],
                    "avatar": user["avatar"],
                    "text": "",
                    "audio_id": audio_id,
                    "time": datetime.now().strftime("%H:%M"),
                }
            )
            st.rerun()


# ==========================================
# TAB 2: PROFILE
# ==========================================
with tab_profile:
    st.subheader("Profile Settings")
    c1, c2 = st.columns([1, 3])
    with c1:
        st.markdown(f"# {user['avatar']}")
    with c2:
        st.markdown(f"### {user['username']}")
        st.caption(f"Role: {user['role']}")

    st.markdown("#### Display Name")
    new_name = st.text_input("Your name", value=user["username"], max_chars=24)
    if st.button("Save Name"):
        name_clean = new_name.strip()
        if not valid_display_name(name_clean):
            st.error("Name must be 1-24 characters.")
        else:
            old_name = user["username"]
            user["username"] = name_clean
            # Update historic messages & audio ownership
            for msg in st.session_state.messages:
                if msg["username"] == old_name:
                    msg["username"] = name_clean
            for item in st.session_state.audio_store.values():
                if item["owner"] == old_name:
                    item["owner"] = name_clean
            st.success("Display name updated!")
            st.rerun()

    st.markdown("#### Choose Avatar")
    cols = st.columns(5)
    for idx, av in enumerate(AVATARS):
        with cols[idx % 5]:
            if st.button(av, key=f"avatar_{av}", use_container_width=True):
                user["avatar"] = av
                # Update historic avatars
                for msg in st.session_state.messages:
                    if msg["username"] == user["username"]:
                        msg["avatar"] = av
                st.rerun()

    if user.get("role") == "host":
        st.divider()
        st.markdown("#### Host Controls")
        if st.button("Clear all messages & audio", type="primary"):
            st.session_state.messages.clear()
            st.session_state.audio_store.clear()
            st.success("All data cleared successfully.")
            st.rerun()
