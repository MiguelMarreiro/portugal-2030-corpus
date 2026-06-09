import streamlit as st
from rag_core import RagEngine
import os

st.set_page_config(page_title="PT2030 & PRR Assistant", page_icon="🇵🇹", layout="centered")

st.title("Portugal 2030 & PRR Funding Assistant 🇵🇹")
st.markdown("Bem-vindo! Pergunte o que quiser sobre os regulamentos, avisos ou manuais do Portugal 2030 e PRR.")

@st.cache_resource
def load_engine():
    # Use Llama 3 for best reasoning in PT
    return RagEngine(model_name="llama3")

engine = load_engine()

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ex: Quais as despesas elegíveis no Inovação Produtiva?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner('A consultar os regulamentos...'):
            response = engine.query(prompt)
            st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
