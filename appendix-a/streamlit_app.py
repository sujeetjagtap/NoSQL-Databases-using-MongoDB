"""Appendix A - Streamlit Chat Frontend

A simple chat UI that connects to the FastAPI backend.
Run: streamlit run streamlit_app.py --server.port 8501
"""

import streamlit as st
import requests

BACKEND_URL = st.secrets.get("BACKEND_URL", "http://localhost:8000")


st.title("NoSQL MongoDB - LLM Chat Application")
st.caption("Powered by RAG + MongoDB Vector Search")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = "session-" + str(hash(st.session_state))

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.session_state.top_k = st.slider("Retrieval Top-K", 1, 10, 3)
    st.text(f"Session: {st.session_state.session_id[:20]}...")
    if st.button("Clear History"):
        st.session_state.messages = []
        st.rerun()

# Health check
try:
    health = requests.get(f"{BACKEND_URL}/health", timeout=3).json()
    st.sidebar.success(f"Backend: {health['llm_backend']}")
except Exception:
    st.sidebar.error("Backend not reachable")

# Chat interface
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg:
            with st.expander("Sources"):
                for s in msg["sources"]:
                    st.write(f"- {s['source']} (score: {s['score']:.4f})")

if prompt := st.chat_input("Ask about NoSQL, MongoDB, AI..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = requests.post(
                    f"{BACKEND_URL}/chat",
                    json={"session_id": st.session_state.session_id, "message": prompt, "top_k": st.session_state.top_k},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                st.markdown(data["response"])
                with st.expander(f"Sources ({len(data['sources'])})"):
                    for s in data["sources"]:
                        st.write(f"- **{s['source']}** (score: {s['score']:.4f})")
                        st.write(f"  > {s['text'][:100]}...")
                st.session_state.messages.append({"role": "assistant", "content": data["response"], "sources": data["sources"]})
            except Exception as e:
                st.error(f"Error: {e}")
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {e}"})
