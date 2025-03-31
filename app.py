import streamlit as st
from bluesky import get_following_list, get_user_posts, get_followers_of_following
from gemini_helper import setup_gemini, analyze_interests, suggest_connections
from atproto import Client
import time
from dotenv import load_dotenv
import os
from database import init_db, verify_user, save_user, save_bluesky_credentials, get_bluesky_credentials
from database import save_following_data, get_following_data, save_potential_connections, get_potential_connections
import json
from streamlit_option_menu import option_menu

# Initialize database
init_db()

# Load environment variables from .env file
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Bluesky Friend Recommender",
    page_icon="👥",
    layout="wide",
)

# Add custom CSS for chat styling
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
    padding: 10px;
    background-color: #222222;
    border-top: 1px solid #444444;
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
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'username' not in st.session_state:
    st.session_state.username = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'following' not in st.session_state:
    st.session_state.following = []
if 'interests_analyzed' not in st.session_state:
    st.session_state.interests_analyzed = False
if 'potential_connections' not in st.session_state:
    st.session_state.potential_connections = []
if 'client' not in st.session_state:
    st.session_state.client = None

# Sidebar navigation using streamlit-option-menu
with st.sidebar:
    st.title("Bluesky Friend Recommender")
    
    # Show login status
    if st.session_state.username:
        st.success(f"Logged in as: {st.session_state.username}")
        if st.button("Logout"):
            st.session_state.username = None
            st.session_state.client = None
            st.session_state.following = []
            st.session_state.interests_analyzed = False
            st.session_state.potential_connections = []
            st.session_state.messages = []
            st.rerun()
    
    # Navigation options with option_menu
    selected = option_menu(
        menu_title="Navigation",
        options=["Login", "User Details", "Following", "Chatbot", "About"],
        icons=["key", "person-fill", "people-fill", "chat-dots-fill", "info-circle-fill"],
        menu_icon="list",
        default_index=0 if not st.session_state.username else 1,
        styles={
            "container": {"padding": "5!important", "background-color": "#262730"},
            "icon": {"color": "orange", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#3e4046"},
            "nav-link-selected": {"background-color": "#0083B8"},
        }
    )
    
    st.markdown("---")
    st.markdown("### Configuration")
    gemini_api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY"), type="password")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)

# Main content based on selection
if selected == "Login":
    st.title("👋 Welcome to Bluesky Friend Recommender")
    
    login_tab, register_tab = st.tabs(["Login", "Register"])
    
    with login_tab:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.username = username
                st.success("Logged in successfully!")
                # Load saved data if available
                following_data = get_following_data(username)
                if following_data:
                    st.session_state.following = following_data
                potential_connections = get_potential_connections(username)
                if potential_connections:
                    st.session_state.potential_connections = potential_connections
                    st.session_state.interests_analyzed = True
                st.rerun()
            else:
                st.error("Invalid credentials")
    
    with register_tab:
        new_username = st.text_input("Username", key="register_username")
        new_password = st.text_input("Password", type="password", key="register_password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        if st.button("Register"):
            if not new_username or not new_password:
                st.error("Username and password are required")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            else:
                save_user(new_username, new_password)
                st.success("Registration successful! You can now login.")

elif selected == "User Details":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("🔑 Bluesky Account Details")
        
        # Get existing credentials if available
        existing_creds = get_bluesky_credentials(st.session_state.username)
        
        bluesky_username = st.text_input(
            "Bluesky Username/Email", 
            value=existing_creds['bluesky_username'] if existing_creds else ""
        )
        bluesky_password = st.text_input(
            "Bluesky Password", 
            value=existing_creds['bluesky_password'] if existing_creds else "",
            type="password"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Save Credentials"):
                save_bluesky_credentials(st.session_state.username, bluesky_username, bluesky_password)
                st.success("Credentials saved successfully!")
        
        with col2:
            if st.button("Fetch Data from Bluesky"):
                with st.spinner("Connecting to Bluesky..."):
                    try:
                        client = Client()
                        client.login(bluesky_username, bluesky_password)
                        st.session_state.client = client
                        
                        # Fetch following list
                        following = get_following_list(client)
                        st.session_state.following = following
                        
                        # Save to database
                        following_data = [
                            {
                                "did": f.did,
                                "handle": f.handle,
                                "display_name": f.display_name
                            } for f in following
                        ]
                        save_following_data(st.session_state.username, following_data)
                        
                        # Get potential connections
                        with st.spinner("Analyzing your network..."):
                            # Set up Gemini if API key is provided
                            if gemini_api_key:
                                model = setup_gemini(gemini_api_key, temperature)
                                
                                # Get posts from people you follow to analyze interests
                                all_posts_data = []
                                for follow in following[:5]:  # Limit to first 5 for demo
                                    posts = get_user_posts(client, follow.did, limit=5)
                                    for post in posts:
                                        if hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                                            all_posts_data.append(f"{follow.handle}: {post.post.record.text}")
                                
                                # Get potential connections for later use
                                potential_connections = []
                                for follow in following[:3]:  # Limit to first 3 for demo
                                    followers = get_followers_of_following(client, follow.did, limit=10)
                                    for follower in followers:
                                        if follower.did != client.me.did:  # Skip yourself
                                            posts = get_user_posts(client, follower.did, limit=3)
                                            post_texts = []
                                            for post in posts:
                                                if hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                                                    post_texts.append(post.post.record.text)
                                            
                                            potential_connections.append({
                                                "did": follower.did,
                                                "handle": follower.handle,
                                                "name": follower.display_name,
                                                "posts": post_texts
                                            })
                                
                                st.session_state.potential_connections = potential_connections
                                save_potential_connections(st.session_state.username, potential_connections)
                                st.session_state.interests_analyzed = True
                        
                        st.success("Data fetched and saved successfully!")
                    except Exception as e:
                        st.error(f"Error connecting to Bluesky: {e}")

elif selected == "Following":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("👥 Accounts You Follow")
        
        # Get following data from database if not in session state
        if not st.session_state.following:
            following_data = get_following_data(st.session_state.username)
            if following_data:
                st.session_state.following = following_data
        
        if not st.session_state.following:
            st.info("No following data available. Please fetch data from the User Details page.")
        else:
            # Display following list
            st.write(f"You follow {len(st.session_state.following)} accounts:")
            
            # Create a search box
            search = st.text_input("Search accounts", "")
            
            # Create a container for the list with scrolling
            following_container = st.container()
            with following_container:
                for follow in st.session_state.following:
                    # If it's a dictionary (from database) or an object (from API)
                    if isinstance(follow, dict):
                        handle = follow.get("handle", "")
                        display_name = follow.get("display_name", "No display name")
                    else:
                        handle = follow.handle
                        display_name = follow.display_name if follow.display_name else "No display name"
                    
                    # Filter by search term if provided
                    if search and search.lower() not in handle.lower() and search.lower() not in display_name.lower():
                        continue
                    
                    # Display the account
                    st.write(f"- **@{handle}** ({display_name})")

elif selected == "Chatbot":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("💬 Friend Recommender Chat")
        
        # Check if we have data to work with
        if not st.session_state.following:
            following_data = get_following_data(st.session_state.username)
            if following_data:
                st.session_state.following = following_data
            else:
                st.info("No following data available. Please fetch data from the User Details page.")
                st.stop()
        
        if not st.session_state.potential_connections:
            connections_data = get_potential_connections(st.session_state.username)
            if connections_data:
                st.session_state.potential_connections = connections_data
                st.session_state.interests_analyzed = True
        
        # Initialize chat if needed
        if not st.session_state.interests_analyzed and gemini_api_key:
            with st.spinner("Analyzing your network..."):
                try:
                    # Set up Gemini
                    model = setup_gemini(gemini_api_key, temperature)
                    
                    # Prepare data for analysis
                    all_posts_data = []
                    if isinstance(st.session_state.following[0], dict):
                        # Data is from database, we need to get posts
                        if st.session_state.client:
                            for follow in st.session_state.following[:5]:
                                posts = get_user_posts(st.session_state.client, follow["did"], limit=5)
                                for post in posts:
                                    if hasattr(post.post, 'record') and hasattr(post.post.record, 'text'):
                                        all_posts_data.append(f"{follow['handle']}: {post.post.record.text}")
                    
                    # Analyze interests if we have post data
                    if all_posts_data:
                        my_interests = analyze_interests(model, "\n".join(all_posts_data))
                    else:
                        my_interests = "Could not analyze interests from available data."
                    
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
            # st.markdown('<div class="chat-container">', unsafe_allow_html=True)
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
        if submit_button and prompt and gemini_api_key:
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            try:
                # Generate response
                model = setup_gemini(gemini_api_key, temperature)
                
                # Format potential connections data
                connections_data = ""
                for conn in st.session_state.potential_connections:
                    if isinstance(conn, dict):
                        handle = conn.get("handle", "")
                        name = conn.get("name", "")
                        posts = conn.get("posts", [])
                    else:
                        handle = conn.handle
                        name = conn.display_name
                        posts = []
                    
                    connections_data += f"User: {handle} ({name})\n"
                    connections_data += f"Posts:\n" + "\n".join(posts) + "\n\n"
                
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

elif selected == "About":
    st.title("ℹ️ About Bluesky Friend Recommender")
    
    st.markdown("""
    ## Features
    
    **Bluesky Friend Recommender** is an AI-powered tool that helps you discover new connections on the Bluesky social network based on your interests and existing network.
    
    ### Key Features:
    
    1. **Network Analysis**: Analyzes your existing following list to understand your interests and social graph.
    
    2. **Interest-Based Recommendations**: Uses AI to identify common interests and themes in your network.
    
    3. **Smart Suggestions**: Recommends new connections based on shared interests and network proximity.
    
    4. **Interactive Chat**: Ask for specific types of connections based on your interests or needs.
    
    5. **Privacy Focused**: Your Bluesky credentials are stored securely and only used to access your network data.
    
    ### How It Works:
    
    1. Log in to your account
    2. Connect your Bluesky account
    3. Let the AI analyze your network
    4. Chat with the assistant to discover new connections
    
    ### Technologies Used:
    
    - Streamlit for the user interface
    - Google's Gemini AI for natural language processing
    - ATProto library for Bluesky API integration
    - SQLite for local data storage
    
    ---
    
    **Created by Mohit Anurag and Abhinandan K23SP**
    """)

# Run the app
if __name__ == "__main__":
    pass