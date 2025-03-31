import streamlit as st
from bluesky import get_following_list, get_user_posts, get_followers_of_following
from gemini_helper import setup_gemini, analyze_interests, suggest_connections
from atproto import Client
import time
from dotenv import load_dotenv
import os

def main():
    # Load environment variables from .env file
    load_dotenv()

    st.title("Bluesky Friend Recommender")
    
    # Add custom CSS for chat styling - only affecting chat elements, not sidebar
    st.markdown("""
    <style>
    /* Chat message styling */
    .user-message {
        background-color: #333333;
        color: #ffffff;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: 0;
        text-align: left;
        border: none;
    }
    
    .assistant-message {
        background-color: #4a4a4a;
        color: #ffffff;
        border-radius: 15px;
        padding: 10px 15px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: auto;
        margin-right: 0;
        text-align: left;
        border: none;
    }
    
    /* Chat container styling */
    .chat-container {
        height: 0vh;
        overflow-y: auto;
        padding-bottom: 0px;
        margin-bottom: 0px;
        background-color: #222222;
    }
    
    /* Input container styling */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 10px;
        background-color: #222222;
        border-top: 1px solid #444444;
        z-index: 1000;
    }
    
    /* Only style the chat input, not sidebar inputs */
    [data-testid="stTextInput"].chat-input > div > div > input {
        border-radius: 20px;
        background-color: #333333;
        color: #ffffff;
        border: 1px solid #444444;
    }
    
    [data-testid="stTextInput"].chat-input > div > div > input::placeholder {
        color: #aaaaaa;
    }
    
    /* Ensure tab content has proper background */
    [data-testid="stTabContent"] {
        background-color: transparent;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        gemini_api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY"), type="password")
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
        
        st.header("Bluesky Login")
        username = st.text_input("Bluesky Username/Email", value=os.getenv("BLUESKY_USERNAME"))
        password = st.text_input("Bluesky Password", value=os.getenv("BLUESKY_PASSWORD"), type="password")
        
        login_button = st.button("Login")
    
    # Initialize session state variables
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    if 'following' not in st.session_state:
        st.session_state.following = []
    
    if 'interests_analyzed' not in st.session_state:
        st.session_state.interests_analyzed = False
    
    if 'potential_connections' not in st.session_state:
        st.session_state.potential_connections = []
    
    # Main content area
    if 'client' not in st.session_state and login_button:
        try:
            client = Client()
            client.login(username, password)
            st.session_state.client = client
            st.success("Successfully logged in!")
        except Exception as e:
            st.error(f"Error logging in: {e}")
    
    if 'client' in st.session_state and gemini_api_key:
        client = st.session_state.client
        
        # Set up tabs
        tab1, tab2 = st.tabs(["Following", "Friend Recommender Chat"])
        
        with tab1:
            st.header("Accounts You Follow")
            following = get_following_list(client)
            st.session_state.following = following
            for follow in following:
                st.write(f"- {follow.handle} ({follow.display_name if follow.display_name else 'No display name'})")
        
        with tab2:
            st.header("Friend Recommender Chat")
            
            # Process data and initialize chat if needed
            if not st.session_state.interests_analyzed:
                with st.spinner("Analyzing your network..."):
                    try:
                        # Set up Gemini
                        model = setup_gemini(gemini_api_key, temperature)
                        
                        # Get posts from people you follow to analyze interests
                        all_posts_data = []
                        for follow in st.session_state.following[:5]:  # Limit to first 5 for demo
                            posts = get_user_posts(client, follow.did, limit=5)
                            for post in posts:
                                if hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                                    all_posts_data.append(f"{follow.handle}: {post.post.record.text}")
                        
                        # Analyze interests
                        my_interests = analyze_interests(model, "\n".join(all_posts_data))
                        
                        # Get potential connections for later use
                        potential_connections = []
                        for follow in st.session_state.following[:3]:  # Limit to first 3 for demo
                            followers = get_followers_of_following(client, follow.did, limit=10)
                            for follower in followers:
                                if follower.did != client.me.did:  # Skip yourself
                                    posts = get_user_posts(client, follower.did, limit=3)
                                    post_texts = []
                                    for post in posts:
                                        if hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                                            post_texts.append(post.post.record.text)
                                    
                                    potential_connections.append({
                                        "handle": follower.handle,
                                        "name": follower.display_name,
                                        "posts": post_texts
                                    })
                        
                        st.session_state.potential_connections = potential_connections
                        
                        # Add initial message from assistant
                        initial_message = f"""👋 Hi there! I'm your Bluesky Friend Assistant. 

I've analyzed your network and found these key interests:
{my_interests}

What kind of friends would you like to connect with?"""
                        
                        st.session_state.messages.append({"role": "assistant", "content": initial_message})
                        st.session_state.interests_analyzed = True
                    except Exception as e:
                        st.error(f"Error analyzing network: {e}")
                        # Add fallback message
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "👋 Hi there! I'm your Bluesky Friend Assistant. What kind of friends are you looking to connect with?"
                        })
                        st.session_state.interests_analyzed = True
            
            # Chat container for messages
            chat_container = st.container()
            with chat_container:
                st.markdown('<div class="chat-container">', unsafe_allow_html=True)
                # Display all messages in the chat history
                for message in st.session_state.messages:
                    if message["role"] == "user":
                        st.markdown(f'<div class="user-message">{message["content"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="assistant-message">{message["content"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Input area at the bottom
            st.markdown('<div class="input-container">', unsafe_allow_html=True)
            
            # Use a form to prevent automatic refreshing
            with st.form(key="chat_form"):
                prompt = st.text_input("", placeholder="Type your friend request or interest...", key="chat_input")
                submit_button = st.form_submit_button("Send")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Process the input only when the form is submitted
            if submit_button and prompt:
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                try:
                    # Generate response
                    model = setup_gemini(gemini_api_key, temperature)
                    
                    # Format potential connections data
                    connections_data = ""
                    for conn in st.session_state.potential_connections:
                        connections_data += f"User: {conn['handle']} ({conn['name']})\n"
                        connections_data += f"Posts:\n" + "\n".join(conn['posts']) + "\n\n"
                    
                    # Create improved prompt for the chatbot
                    combined_prompt = f"""You are a friend recommendation expert for Bluesky social network.

USER QUERY: "{prompt}"

AVAILABLE CONNECTIONS:
{connections_data}

INSTRUCTIONS:
- If the query is about finding friends or interests, recommend 2-3 relevant connections
- Include handle, name, and brief reason for each recommendation
- If the query is unrelated to friend recommendations, respond with:
  "I focus on helping you find friends on Bluesky. How about telling me what interests you'd like to explore?"
- Keep responses under 100 words
- Do not mention being an AI
"""
                    
                    # Generate response based on user input
                    response = model.generate_content(combined_prompt)
                    response_text = response.text
                    
                    # Add assistant response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": response_text})
                except Exception as e:
                    # Fallback response if Gemini fails
                    fallback = "I'm having trouble processing that request. Could you try asking about specific interests you'd like to explore?"
                    st.session_state.messages.append({"role": "assistant", "content": fallback})
                
                # Force a rerun to update the chat without modifying session state
                st.rerun()

if __name__ == "__main__":
    main()