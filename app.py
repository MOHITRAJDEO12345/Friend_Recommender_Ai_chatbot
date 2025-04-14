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
from reddit import get_reddit_client, get_subscribed_subreddits
from database import save_reddit_credentials, get_reddit_credentials, save_reddit_subscriptions, get_reddit_subscriptions

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

# Update the custom CSS for chat styling at the beginning of the file
st.markdown("""
<style>
/* Chat message styling */
.user-message {
    background-color: #2b5797;
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

.assistant-message {
    background-color: #383838;
    color: #ffffff;
    border-radius: 15px;
    padding: 10px 15px;
    margin: 5px 0;
    max-width: 80%;
    margin-left: 0;
    text-align: left;
    border: none;
}

/* Chat container styling */
.chat-container {
    height: 60vh;
    overflow-y: auto;
    padding-bottom: 20px;
    margin-bottom: 20px;
    background-color: #111111;
    border-radius: 10px;
}

/* Input container styling */
.input-container {
    padding: 10px;
    background-color: #111111;
    border-top: 1px solid #444444;
    border-radius: 10px;
}

/* Prompt box styling */
.prompt-box { 
    background-color: #222222; 
    padding: 12px; 
    border-radius: 8px; 
    font-size: 14px; 
    font-family: sans-serif;
    margin-bottom: 10px;
    border: 1px solid #444444;
    text-align: center;
    cursor: pointer;
    transition: background-color 0.3s;
}

.prompt-box:hover {
    background-color: #333333;
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
    st.title("Friend Recommender AI")
    
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
            # Clear Reddit session state as well
            if 'reddit_subscriptions' in st.session_state:
                st.session_state.reddit_subscriptions = []
            st.rerun()
    
    # Navigation options with option_menu
    selected = option_menu(
        menu_title="Navigation",
        options=["Login", "User Details", "Following", "Recommendations", "Chatbot", "About"],
        icons=["key", "person-fill", "people-fill", "lightbulb-fill", "chat-dots-fill", "info-circle-fill"],
        menu_icon="list",
        default_index=0 if not st.session_state.username else 1,
        styles={
            "container": {"padding": "5!important", "background-color": "#262730"},
            "icon": {"color": "#FF5555", "font-size": "25px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#3e4046"},
            "nav-link-selected": {"background-color": "#CC0000"},
        }
    )
    
    st.markdown("---")
    st.markdown("### Configuration")
    gemini_api_key = st.text_input("Gemini API Key", value=os.getenv("GEMINI_API_KEY"), type="password")
    temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7, step=0.1)
    

# Main content based on selection
if selected == "Login":
    st.title("👋 Welcome to Friend Recommender Chatbot")
    
    # Add a short description below the title
    st.markdown("Discover new friends and connections on Bluesky and Reddit based on your interests and network.")

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

    # Add footer text below the login section
    st.markdown(" CREATED BY: MOHIT 12323329 , ANURAG 12304680, ABHINANDAN 12323328")
    st.markdown("""    ### How It Works:
    
    1. Log in to your account
    2. Connect your Bluesky and/or Reddit accounts
    3. Let the AI analyze your network
    4. View recommendations in the dedicated section
    5. Chat with the assistant to discover new connections
    """)

elif selected == "User Details":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("🔑 Account Details")
        
        # Create tabs for different platforms
        bluesky_tab, reddit_tab = st.tabs(["Bluesky", "Reddit"])
        
        with bluesky_tab:
            st.subheader("Bluesky Account")
            # Get existing credentials if available
            existing_creds = get_bluesky_credentials(st.session_state.username)
            
            bluesky_username = st.text_input(
                "Bluesky Username/Email", 
                value=existing_creds['bluesky_username'] if existing_creds else "",
                key="bluesky_username"
            )
            bluesky_password = st.text_input(
                "Bluesky Password", 
                value=existing_creds['bluesky_password'] if existing_creds else "",
                type="password",
                key="bluesky_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save Bluesky Credentials"):
                    save_bluesky_credentials(st.session_state.username, bluesky_username, bluesky_password)
                    st.success("Bluesky credentials saved successfully!")
            
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
        
        with reddit_tab:
            st.subheader("Reddit Account")
            # Get existing Reddit credentials if available
            existing_reddit_creds = get_reddit_credentials(st.session_state.username)
            
            reddit_username = st.text_input(
                "Reddit Username", 
                value=existing_reddit_creds['reddit_username'] if existing_reddit_creds else "",
                key="reddit_username"
            )
            reddit_password = st.text_input(
                "Reddit Password", 
                value=existing_reddit_creds['reddit_password'] if existing_reddit_creds else "",
                type="password",
                key="reddit_password"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Save Reddit Credentials"):
                    save_reddit_credentials(st.session_state.username, reddit_username, reddit_password)
                    st.success("Reddit credentials saved successfully!")
            
            with col2:
                if st.button("Fetch Reddit Subscriptions"):
                    with st.spinner("Connecting to Reddit..."):
                        try:
                            reddit_client = get_reddit_client(reddit_username, reddit_password)
                            if reddit_client:
                                # Fetch subscribed subreddits
                                subreddits = get_subscribed_subreddits(reddit_client)
                                st.session_state.reddit_subscriptions = subreddits
                                
                                # Save to database
                                save_reddit_subscriptions(st.session_state.username, subreddits)
                                
                                st.success(f"Successfully fetched {len(subreddits)} subreddit subscriptions!")
                            else:
                                st.error("Failed to initialize Reddit client. Please check your credentials.")
                        except Exception as e:
                            st.error(f"Error connecting to Reddit: {e}")

# Add a new section in the sidebar for Reddit subscriptions
elif selected == "Following":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("👥 Following")
        
        # Create tabs for different platforms
        bluesky_tab, reddit_tab = st.tabs(["Bluesky Following", "Reddit Subscriptions"])
        
        with bluesky_tab:
            # Check if we have following data
            if not st.session_state.following:
                following_data = get_following_data(st.session_state.username)
                if following_data:
                    st.session_state.following = following_data
                else:
                    st.info("No following data available. Please fetch data from the User Details page.")
                    st.stop()
            
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
                        # For ProfileView objects, use attribute access instead of .get()
                        handle = getattr(follow, "handle", "unknown")
                        display_name = getattr(follow, "display_name", "No display name")
                    
                    # Filter by search term if provided
                    if search and search.lower() not in handle.lower() and search.lower() not in display_name.lower():
                        continue
                    
                    # Display the account - use the variables we've safely extracted
                    st.write(f"**{display_name}** (@{handle})")

        with reddit_tab:
            # Get Reddit subscriptions from database if not in session state
            if not hasattr(st.session_state, 'reddit_subscriptions') or not st.session_state.reddit_subscriptions:
                reddit_subs = get_reddit_subscriptions(st.session_state.username)
                if reddit_subs:
                    st.session_state.reddit_subscriptions = reddit_subs
            
            if not hasattr(st.session_state, 'reddit_subscriptions') or not st.session_state.reddit_subscriptions:
                st.info("No Reddit subscription data available. Please fetch data from the User Details page.")
            else:
                # Display subreddit subscriptions
                st.write(f"You are subscribed to {len(st.session_state.reddit_subscriptions)} subreddits:")
                
                # Create a search box for Reddit
                reddit_search = st.text_input("Search subreddits", "")
                
                # Display subreddits in a nice format
                for i, subreddit in enumerate(st.session_state.reddit_subscriptions):
                    # Filter by search term if provided
                    subreddit_name = subreddit.get('name', '')
                    if reddit_search and reddit_search.lower() not in subreddit_name.lower():
                        continue
                        
                    with st.container():
                        col1, col2 = st.columns([1, 3])
                        with col1:
                            st.write(f"**r/{subreddit_name}**")
                        with col2:
                            st.write(f"Subscribers: {subreddit.get('subscribers', 'Unknown')}")
                            st.write(f"{subreddit.get('description', '')}")
                        st.divider()

elif selected == "Recommendations":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("💡 Friend Recommendations")
        
        # Initialize session state for recommendations if not exists
        if "bluesky_recommendations" not in st.session_state:
            st.session_state.bluesky_recommendations = []
        if "reddit_recommendations" not in st.session_state:
            st.session_state.reddit_recommendations = []
        if "bluesky_interests" not in st.session_state:
            st.session_state.bluesky_interests = ""
        if "reddit_interests" not in st.session_state:
            st.session_state.reddit_interests = ""
        
        # Create tabs for different platforms
        bluesky_tab, reddit_tab = st.tabs(["Bluesky Recommendations", "Reddit Recommendations"])
        
        # Check if we have Gemini API key
        if not gemini_api_key:
            st.error("Please provide a Gemini API key in the sidebar to generate recommendations.")
            st.stop()
        
        # Set up Gemini model
        try:
            model = setup_gemini(gemini_api_key, temperature)
        except Exception as e:
            st.error(f"Error setting up Gemini model: {e}")
            st.stop()
        
        # Fetch data and generate recommendations
        with st.spinner("Analyzing your interests and generating recommendations..."):
            # 1. Fetch Bluesky data
            following_data = get_following_data(st.session_state.username)
            potential_connections = get_potential_connections(st.session_state.username)
            
            # 2. Fetch Reddit data
            reddit_subs = get_reddit_subscriptions(st.session_state.username)
            
            # Check if we have data to analyze
            has_bluesky_data = bool(following_data and potential_connections)
            has_reddit_data = bool(reddit_subs)
            
            if not has_bluesky_data and not has_reddit_data:
                st.warning("No data available. Please fetch data from the User Details page first.")
                st.stop()
            
            # 3. Generate interests and recommendations
            
            # For Bluesky
            with bluesky_tab:
                if has_bluesky_data:
                    # Generate interests if not already done
                    if not st.session_state.bluesky_interests:
                        # Prepare data for analysis - extract posts from potential connections
                        all_posts_data = []
                        for conn in potential_connections[:5]:  # Limit to first 5 for performance
                            if isinstance(conn, dict) and "posts" in conn:
                                for post in conn.get("posts", []):
                                    all_posts_data.append(f"{conn.get('handle', 'unknown')}: {post}")
                        
                        if all_posts_data:
                            # Extract interests using Gemini
                            st.session_state.bluesky_interests = analyze_interests(model, "\n".join(all_posts_data))
                    
                    # Display interests
                    st.subheader("Your Bluesky Interests")
                    st.write(st.session_state.bluesky_interests)
                    
                    # Generate recommendations if not already done
                    if not st.session_state.bluesky_recommendations:
                        # Format potential connections for recommendation
                        connections_data = ""
                        for conn in potential_connections:
                            if isinstance(conn, dict):
                                handle = conn.get("handle", "")
                                name = conn.get("name", "")
                                posts = conn.get("posts", [])
                                
                                connections_data += f"User: {handle} ({name})\n"
                                connections_data += f"Posts:\n" + "\n".join(posts[:2]) + "\n\n"  # Limit to 2 posts
                        
                        # Get recommendations from Gemini
                        if connections_data and st.session_state.bluesky_interests:
                            recommendations = suggest_connections(
                                model, 
                                st.session_state.bluesky_interests, 
                                connections_data
                            )
                            st.session_state.bluesky_recommendations = recommendations
                    
                    # Display recommendations
                    st.subheader("Recommended Bluesky Connections")
                    if st.session_state.bluesky_recommendations:
                        st.markdown(st.session_state.bluesky_recommendations)
                    else:
                        st.info("No Bluesky recommendations available yet.")
                    
                    # Add refresh button
                    if st.button("Refresh Bluesky Recommendations"):
                        st.session_state.bluesky_interests = ""
                        st.session_state.bluesky_recommendations = []
                        st.rerun()
                else:
                    st.info("No Bluesky data available. Please fetch data from the User Details page.")
            
            # For Reddit
            with reddit_tab:
                if has_reddit_data:
                    # Generate interests if not already done
                    if not st.session_state.reddit_interests:
                        # Prepare data for analysis
                        subreddit_data = []
                        for sub in reddit_subs[:10]:  # Limit to first 10 for performance
                            if isinstance(sub, dict):
                                name = sub.get("name", "")
                                description = sub.get("description", "")
                                subreddit_data.append(f"r/{name}: {description}")
                        
                        if subreddit_data:
                            # Extract interests using Gemini
                            st.session_state.reddit_interests = analyze_interests(model, "\n".join(subreddit_data))
                    
                    # Display interests
                    st.subheader("Your Reddit Interests")
                    st.write(st.session_state.reddit_interests)
                    
                    # Generate recommendations if not already done
                    if not st.session_state.reddit_recommendations:
                        # Format subreddit data for recommendation
                        subreddit_info = ""
                        for sub in reddit_subs:
                            if isinstance(sub, dict):
                                name = sub.get("name", "")
                                description = sub.get("description", "")
                                subscribers = sub.get("subscribers", "Unknown")
                                
                                subreddit_info += f"Subreddit: r/{name}\n"
                                subreddit_info += f"Subscribers: {subscribers}\n"
                                subreddit_info += f"Description: {description}\n\n"
                        
                        # Get recommendations from Gemini
                        if subreddit_info and st.session_state.reddit_interests:
                            # Custom prompt for Reddit recommendations
                            prompt = f"""
                            Based on the following interests:
                            {st.session_state.reddit_interests}
                            
                            And these subreddits the user is subscribed to:
                            {subreddit_info}
                            
                            Suggest 5 people/accounts they might want to follow on Reddit based on these interests.
                            For each suggestion:
                            1. Provide a username (can be fictional but realistic)
                            2. Explain why they would be a good connection
                            3. Mention which subreddits they're likely active in
                            
                            Format each suggestion with a clear heading and bullet points.
                            """
                            
                            try:
                                response = model.generate_content(prompt)
                                st.session_state.reddit_recommendations = response.text
                            except Exception as e:
                                st.session_state.reddit_recommendations = "Could not generate Reddit recommendations at this time."
                    
                    # Display recommendations
                    st.subheader("Recommended Reddit Connections")
                    if st.session_state.reddit_recommendations:
                        st.markdown(st.session_state.reddit_recommendations)
                    else:
                        st.info("No Reddit recommendations available yet.")
                    
                    # Add refresh button
                    if st.button("Refresh Reddit Recommendations"):
                        st.session_state.reddit_interests = ""
                        st.session_state.reddit_recommendations = []
                        st.rerun()
                else:
                    st.info("No Reddit data available. Please fetch data from the User Details page.")

elif selected == "Chatbot":
    if not st.session_state.username:
        st.warning("Please login first")
    else:
        st.title("💬 Friend Recommender Chat")
        st.markdown("### Chat with our AI to find personalized friend recommendations")
        st.write("Ask about **interests, topics, or specific types of accounts you'd like to follow on Bluesky or Reddit.**")
        
        # Check if we have data to work with
        if not st.session_state.following:
            following_data = get_following_data(st.session_state.username)
            if following_data:
                st.session_state.following = following_data
            else:
                st.info("No following data available. Please fetch data from the User Details page.")
        
        if not st.session_state.potential_connections:
            connections_data = get_potential_connections(st.session_state.username)
            if connections_data:
                st.session_state.potential_connections = connections_data
                st.session_state.interests_analyzed = True
        
        # Check for Reddit data
        if not st.session_state.reddit_subscriptions:
            reddit_subs = get_reddit_subscriptions(st.session_state.username)
            if reddit_subs:
                st.session_state.reddit_subscriptions = reddit_subs
        
        # Custom Styling for prompt suggestions
        st.markdown("""
            <style>
                .prompt-box { 
                    background-color: #222222; 
                    padding: 12px; 
                    border-radius: 8px; 
                    font-size: 14px; 
                    font-family: sans-serif;
                    margin-bottom: 10px; 
                    border: 1px solid #444444;
                    text-align: center;
                    cursor: pointer;
                }
                .prompt-box:hover {
                    background-color: #333333;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # Common prompt suggestions
        st.markdown("#### 💡 Common Questions")
        
        prompt_options = [
            ("Bluesky Tech", "Who should I follow for tech news on Bluesky?"),
            ("Reddit Tech", "Recommend Reddit users for tech discussions"),
            ("Bluesky Art", "Find me Bluesky users interested in digital art"),
            ("Reddit Gaming", "Who are good Reddit users to follow for gaming content?"),
            ("Bluesky News", "Who are good Bluesky accounts for news updates?"),
            ("Reddit Science", "Suggest Reddit users who post about scientific research"),
            ("Bluesky Photography", "Recommend photographers on Bluesky I should follow"),
            ("Reddit Writing", "Find me Reddit users who write about fiction"),
            ("Bluesky Food", "Suggest Bluesky accounts that share recipes"),
            ("Reddit Travel", "I want to follow Reddit users who post about travel")
        ]
        
        # Display prompts in two columns (2 prompts per row)
        cols = st.columns(2)
        for i in range(0, len(prompt_options), 2):
            with cols[0]: 
                if i < len(prompt_options):
                    label, prompt = prompt_options[i]
                    st.markdown(f"""<div class="prompt-box" onclick="document.querySelector('#chat-input').value='{prompt}';"><strong>{label}</strong><br>{prompt}</div>""", unsafe_allow_html=True)
            
            with cols[1]: 
                if i+1 < len(prompt_options):
                    label, prompt = prompt_options[i+1]
                    st.markdown(f"""<div class="prompt-box" onclick="document.querySelector('#chat-input').value='{prompt}';"><strong>{label}</strong><br>{prompt}</div>""", unsafe_allow_html=True)
        
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
                    initial_message = f"""👋 Hi there! I'm your Friend Recommendation Assistant. 

I've analyzed your network and found these key interests:
{my_interests}

What kind of friends would you like to connect with on Bluesky or Reddit?"""
                    
                    st.session_state.messages.append({"role": "assistant", "content": initial_message})
                    st.session_state.interests_analyzed = True
                except Exception as e:
                    st.error(f"Error analyzing network: {e}")
                    # Add fallback message
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "👋 Hi there! I'm your Friend Recommendation Assistant. What kind of friends are you looking to connect with on Bluesky or Reddit?"
                    })
                    st.session_state.interests_analyzed = True
        
        # Chat container
        chat_container = st.container()
        with chat_container:
            # Display chat messages using the new chat_message component
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        
        # User input with chat_input
        user_input = st.chat_input("Ask about interests, topics, or specific types of accounts...", key="chat_input")
        
        # Process the input
        if user_input and gemini_api_key:
            # Display user message
            with st.chat_message("user"):
                st.markdown(user_input)
            
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            try:
                # Generate response
                model = setup_gemini(gemini_api_key, temperature)
                
                # Format potential connections data for Bluesky
                bluesky_connections_data = ""
                if st.session_state.potential_connections:
                    bluesky_connections_data = "BLUESKY CONNECTIONS:\n"
                    for conn in st.session_state.potential_connections:
                        if isinstance(conn, dict):
                            handle = conn.get("handle", "")
                            name = conn.get("name", "")
                            posts = conn.get("posts", [])
                        else:
                            handle = conn.handle
                            name = conn.display_name
                            posts = []
                        
                        bluesky_connections_data += f"User: {handle} ({name})\n"
                        bluesky_connections_data += f"Posts:\n" + "\n".join(posts) + "\n\n"
                
                # Format Reddit subscriptions data
                reddit_data = ""
                if hasattr(st.session_state, 'reddit_subscriptions') and st.session_state.reddit_subscriptions:
                    reddit_data = "REDDIT SUBSCRIPTIONS:\n"
                    for sub in st.session_state.reddit_subscriptions[:10]:  # Limit to 10 for performance
                        reddit_data += f"Subreddit: r/{sub.get('name', '')}\n"
                        reddit_data += f"Description: {sub.get('description', '')}\n\n"
                
                # Create improved prompt for the chatbot
                combined_prompt = f"""You are a friend recommendation expert for both Bluesky and Reddit social networks.

USER QUERY: "{user_input}"

{bluesky_connections_data}

{reddit_data}

INSTRUCTIONS:
- STRICTLY ONLY respond to queries about finding friends, connections, or accounts to follow on Bluesky or Reddit
- If the query mentions Bluesky, recommend 2-3 relevant Bluesky connections
- If the query mentions Reddit, recommend 2-3 relevant Reddit users based on their subreddit interests
- If the query doesn't specify a platform, provide recommendations for both platforms if possible
- Include handle/username, name, and brief reason for each recommendation
- For ANY query not DIRECTLY related to finding friends/connections on Bluesky or Reddit, respond ONLY with:
  "I focus on helping you find friends on Bluesky and Reddit. How about telling me what interests you'd like to explore?"
- This includes general questions, greetings, personal questions, or any topic not specifically about finding accounts to follow
- Keep responses under 150 words
- Do not mention being an AI
- Do not engage in small talk or answer questions outside the scope of friend recommendations
"""
                
                # Generate response based on user input
                response = model.generate_content(combined_prompt)
                response_text = response.text
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response_text})
                
                # Display assistant's response
                with st.chat_message("assistant"):
                    st.markdown(response_text)
                
            except Exception as e:
                # Fallback response if Gemini fails
                fallback = "I'm having trouble processing that request. Could you try asking about specific interests you'd like to explore on Bluesky or Reddit?"
                st.session_state.messages.append({"role": "assistant", "content": fallback})
                
                with st.chat_message("assistant"):
                    st.markdown(fallback)
            
            # Force a rerun to update the chat
            st.rerun()

elif selected == "About":
    st.title("ℹ️ About Friend Recommender AI")
    
    st.markdown("""
    ## Features
    
    **Friend Recommender AI** is an intelligent tool that helps you discover new connections on both Bluesky and Reddit social networks based on your interests and existing network.
    
    ### Key Features:
    
    1. **Multi-Platform Support**: Connect both your Bluesky and Reddit accounts to get personalized recommendations across platforms.
    
    2. **Network Analysis**: Analyzes your existing following list and subreddit subscriptions to understand your interests and social graph.
    
    3. **Interest-Based Recommendations**: Uses AI to identify common interests and themes in your network.
    
    4. **Smart Suggestions**: Recommends new connections based on shared interests and network proximity.
    
    5. **Interactive Chat**: Ask for specific types of connections based on your interests or needs on either platform.
    
    6. **Dedicated Recommendation Tabs**: View separate recommendation sections for Bluesky and Reddit connections.
    
    7. **Privacy Focused**: Your credentials are stored securely and only used to access your network data.
    
    ### Technologies Used:
    
    - Streamlit for the user interface
    - Google's Gemini AI for natural language processing and recommendations
    - ATProto library for Bluesky API integration
    - PRAW (Python Reddit API Wrapper) for Reddit integration
    - SQLite for local data storage
    
    ---
    
    **Created by:
    Mohit Raj Deo
    Anurag Shukla 
    Abhinandan Choudhary
    K23MW**
    """)

# Run the app
if __name__ == "__main__":
    pass