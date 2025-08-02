import streamlit as st
import json
from datetime import datetime
import uuid
import asyncio
import websockets
from typing import Optional
import threading
from concurrent.futures import ThreadPoolExecutor

# Page configuration
st.set_page_config(
    page_title="AI Quotation Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# WebSocket communication function
def send_websocket_message(websocket_url: str, message_payload: dict, timeout: int = 30) -> Optional[str]:
    """Send message via WebSocket and return response"""
    async def _send_message():
        try:
            async with websockets.connect(websocket_url) as websocket:
                # Send message
                await websocket.send(json.dumps(message_payload))
                
                # Wait for response with timeout
                response = await asyncio.wait_for(
                    websocket.recv(),
                    timeout=timeout
                )
                return response
        except Exception as e:
            raise e
    
    # Run the async function in a new event loop
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(_send_message())
    except Exception as e:
        raise e
    finally:
        loop.close()

# Configuration
WEBSOCKET_URL = st.sidebar.text_input(
    "WebSocket URL",
    value="ws://localhost:8000/ws/chat",
    help="Enter the WebSocket URL of your AI agent"
)

REQUEST_TIMEOUT = st.sidebar.slider(
    "Request Timeout (seconds)",
    min_value=5,
    max_value=60,
    value=30,
    help="How long to wait for agent response"
)

# Sidebar info
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
st.sidebar.markdown(f"**Messages:** {len(st.session_state.messages)}")

# Clear chat button
if st.sidebar.button("Clear Chat", type="secondary"):
    st.session_state.messages = []
    
    # Also clear the backend conversation
    clear_payload = {
        "session_id": st.session_state.session_id,
        "message": "/clear",
        "timestamp": datetime.now().isoformat(),
        "user_id": "streamlit_user",
        "message_type": "clear"
    }
    
    try:
        # Send clear command via WebSocket
        clear_response = send_websocket_message(WEBSOCKET_URL, clear_payload, REQUEST_TIMEOUT)
        if clear_response:
            response_data = json.loads(clear_response)
            st.sidebar.success("Chat cleared on backend")
    except Exception as e:
        st.sidebar.warning(f"Failed to clear backend: {str(e)}")
    
    st.rerun()

# Main chat interface
st.title("🤖 AI Quotation Agent")
st.markdown("Paste in your client's requirements and get a quote!")
st.markdown("""
You can converse with the AI agent to give it more context or ask questions about the quote.
""")

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"_{message['timestamp']}_")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    # Add user message to chat
    timestamp = datetime.now().strftime("%H:%M:%S")
    user_message = {
        "role": "user",
        "content": prompt,
        "timestamp": timestamp
    }
    st.session_state.messages.append(user_message)
    
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(f"_{timestamp}_")
    
    # Prepare WebSocket message payload
    message_payload = {
        "session_id": st.session_state.session_id,
        "message": prompt,
        "timestamp": datetime.now().isoformat(),
        "user_id": "streamlit_user",
        "message_type": "chat"
    }
    
    # Show loading spinner and send WebSocket message
    with st.chat_message("assistant"):
        with st.spinner("Agent is thinking..."):
            try:
                # Send message via WebSocket
                agent_response = send_websocket_message(WEBSOCKET_URL, message_payload, REQUEST_TIMEOUT)
                
                if agent_response:
                    # Parse response
                    response_data = json.loads(agent_response)
                    agent_message = response_data.get("message", "No response from agent")
                    
                    # Display agent response
                    st.markdown(agent_message)
                    response_timestamp = datetime.now().strftime("%H:%M:%S")
                    st.caption(f"_{response_timestamp}_")
                    
                    # Add agent message to session state
                    assistant_message = {
                        "role": "assistant",
                        "content": agent_message,
                        "timestamp": response_timestamp
                    }
                    st.session_state.messages.append(assistant_message)
                    
                else:
                    error_msg = "No response received from agent"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
            except Exception as e:
                error_msg = f"WebSocket error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
    
    # Rerun to update the chat display
    st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.8em;'>
        AI Agent Chat Interface | Built by <a href='https://tomshaw.dev' target='_blank' style='color: lightblue; text-decoration: underline;'>Tom Shaw</a>
    </div>
    """,
    unsafe_allow_html=True
)
