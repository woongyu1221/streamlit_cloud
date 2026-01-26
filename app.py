import streamlit as st
from openai import OpenAI
import os

# Page configuration
st.set_page_config(
    page_title="AI Developer Assistant",
    page_icon="🤖",
    layout="wide"
)

# Sidebar settings
with st.sidebar:
    st.title("Settings")
    
    # Model Selection
    model_options = [
        "google/gemini-2.0-flash-exp:free",
        "openai/gpt-oss-120b:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "google/gemini-2.0-flash-thinking-exp:free" 
    ]
    selected_model = st.selectbox(
        "Select Model", 
        model_options, 
        index=0,
        help="Select the AI model to use from OpenRouter."
    )
    
    show_reasoning = st.toggle("Display Reasoning Logic", value=False)
    st.markdown("---")
    st.caption(f"Current Model: `{selected_model}`")

# Initialize client using st.secrets for Cloud deployment
# Fallback to os.getenv for local development if not in secrets
api_key = st.secrets.get("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY"))

if not api_key:
    st.error("🚨 API Key not found! Please set `OPENROUTER_API_KEY` in Streamlit Secrets.")
    st.stop()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Persona definition
SYSTEM_PROMPT = """You are an AI Developer Assistant. 
Your goal is to help users with coding tasks, debugging, and software architecture.
You must answer all questions in Korean.
Be concise, technical, and helpful.
Use Markdown for code blocks.
"""

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Display chat history (excluding system prompt)
st.title("🤖 AI Developer Assistant")
st.caption("Powered by OpenRouter & Streamlit Cloud")

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # Display reasoning if stored in history and toggle is on
            if show_reasoning and "reasoning_details" in message and message["reasoning_details"]:
                with st.expander("Reasoning Process (Saved)", expanded=False):
                    try:
                        st.write(message["reasoning_details"])
                    except:
                        st.info("Raw reasoning data unavailable.")

# Chat input
if prompt := st.chat_input("질문을 입력하세요..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Prepare messages (filtering for compatibility)
            api_messages = []
            for msg in st.session_state.messages:
                m = {"role": msg["role"], "content": msg["content"]}
                # Pass reasoning details back if the model supports it/needs it to maintain context
                # Note: Standard OpenAI API might reject unknown keys, but OpenRouter often proxies them.
                # If issues arise, we might need to strictly filter 'role' and 'content' only.
                # For now, we'll keep it simple as per user snippet logic.
                if "reasoning_details" in msg:
                     m["reasoning_details"] = msg["reasoning_details"]
                api_messages.append(m)

            response = client.chat.completions.create(
                model=selected_model,
                messages=api_messages,
                extra_body={
                    "reasoning": {"enabled": True} if show_reasoning or "thinking" in selected_model else {"enabled": False}
                }
            )

            # Process response
            result_message = response.choices[0].message
            full_response = result_message.content
            
            # Check for reasoning details (OpenRouter/specific models)
            reasoning_details = getattr(result_message, "reasoning_details", None)

            message_placeholder.markdown(full_response)
            
            if show_reasoning and reasoning_details:
                with st.expander("Reasoning Process", expanded=True):
                    st.write(reasoning_details)

            # Add assistant message to history
            st.session_state.messages.append({
                "role": "assistant", 
                "content": full_response,
                "reasoning_details": reasoning_details
            })

        except Exception as e:
            st.error(f"Error: {str(e)}")
