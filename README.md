# 📘 Friend Recommender AI
https://friend-recommender-ai-chatbot.streamlit.app/

AI-powered Friend Recommender System to help users discover potential connections on **Bluesky** and **Reddit** based on their social graph and interests. Built with **Streamlit**, **Google Gemini API**, and integrated with **Bluesky** and **Reddit** using respective APIs.

---

## 🚀 Project Overview

**Goal:** Recommend like-minded friends or communities on Bluesky and Reddit using network analysis and generative AI.

### 🛠️ Tech Stack
- **Frontend:** Streamlit
- **AI Model:** Gemini (Google's LLM API)
- **APIs:**
  - Bluesky via ATProto client
  - Reddit via PRAW
- **Database:** SQLite (local)

---

## 🔑 Core Features

### 1. 🔐 User Authentication
- Register/Login via Streamlit form.
- Securely store usernames and hashed passwords using SQLite.

### 2. 🔗 Multi-Platform Integration
- **Bluesky:** Enter credentials → fetch followings, posts, and extended network.
- **Reddit:** Login via PRAW → fetch subscribed subreddits.

### 3. 📡 Data Fetching
- **Bluesky:**
  - `get_following_list()`
  - `get_user_posts()`
  - `get_followers_of_following()`
- **Reddit:**
  - `get_subscribed_subreddits()`

### 4. 🧠 Interest Extraction (Gemini API)
- Extract interests from Bluesky posts and Reddit subreddit descriptions.
- Format as emoji-rich bullet list.

### 5. 🤝 AI-Powered Recommendations
- Analyze interests + 2nd-degree connections.
- Recommend:
  - Bluesky users
  - Reddit communities or usernames

### 6. 💬 Chatbot Assistant
- Ask questions like:
  - “Suggest Bluesky users into AI”
  - “Communities for photography on Reddit”
- Powered by Gemini with prompt engineering.

### 7. 🧭 Streamlit Navigation
- Login
- User Details
- Following
- Recommendations
- Chatbot
- About

### 8. 🗃️ Database Handling (SQLite)
- Stores:
  - Users & passwords
  - Platform credentials
  - Fetched data
  - Recommendations

### 9. 📦 Modular Structure
```
FriendRecommenderAI/
├── app.py                 # Main Streamlit UI
├── database.py           # DB logic
├── bluesky.py            # Bluesky API helpers
├── reddit.py             # Reddit API helpers
├── gemini_helper.py      # Gemini prompt logic
├── requirements.txt
└── README.md
```

---

## 🔄 Flow Summary

```text
User → [Login/Register] → SQLite DB
     → [Enter Social Credentials] → Bluesky + Reddit APIs
     → [Fetch Network Data] → Save to SQLite
     → [Analyze Interests w/ Gemini] ← Post/Subreddit Data
     → [Generate Recommendations w/ Gemini] → Show to User
     → [Chatbot Interaction] → Gemini Response
     → [Store Everything for Future Use]
```

---

## 🧪 Example Prompts for Chatbot
```
- Find Bluesky users interested in AI 🤖
- Suggest Reddit communities about travel ✈️
- I want to connect with tech & productivity folks 👨‍💻
```

---

## ⚙️ Installation
```bash
# Clone repo
$ git clone https://github.com/your-username/FriendRecommenderAI.git
$ cd FriendRecommenderAI

# Create and activate virtual environment
$ python -m venv venv
$ source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
$ pip install -r requirements.txt

# Run Streamlit app
$ streamlit run app.py
```

---

## 🔐 Setup Credentials

### Gemini API
- Get API Key from https://makersuite.google.com/app
- Set it in `gemini_helper.py`:
```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")
```

### Reddit
- Register app at https://www.reddit.com/prefs/apps
- Use the credentials in `reddit.py`
```python
reddit = praw.Reddit(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_SECRET",
    user_agent="YOUR_USER_AGENT",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
)
```

### Bluesky
- Use ATProto client credentials (username, app password)

---

## 📈 Future Extensions
- 🔗 Twitter/X integration
- 📊 D3.js or Graphviz-based visualizations
- ☁️ Cloud deployment with Docker & GCP
- 📱 Mobile responsiveness

---

## 👨‍💻 Authors
- Mohit (12323329)
- Anurag (12304680)
- Abhinandan (12323328)

---

## 📜 License
MIT License

---

## 💬 Need Help?
Drop your questions, feature requests, or bugs in the Issues section!

---

**Made with 💡 using Streamlit, Gemini, Bluesky & Reddit.**

