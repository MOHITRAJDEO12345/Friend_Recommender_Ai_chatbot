import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bluesky_recommender.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users table for login/registration
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT)''')
    
    # Bluesky credentials table
    c.execute('''CREATE TABLE IF NOT EXISTS bluesky_credentials
                 (username TEXT PRIMARY KEY,
                  bluesky_username TEXT,
                  bluesky_password TEXT)''')
    
    # Reddit credentials table
    c.execute('''CREATE TABLE IF NOT EXISTS reddit_credentials
                 (username TEXT PRIMARY KEY,
                  reddit_username TEXT,
                  reddit_password TEXT)''')
    
    # Following data table
    c.execute('''CREATE TABLE IF NOT EXISTS following_data
                 (username TEXT,
                  following_data TEXT,
                  PRIMARY KEY (username))''')
    
    # Reddit subscriptions table
    c.execute('''CREATE TABLE IF NOT EXISTS reddit_subscriptions
                 (username TEXT,
                  subscriptions_data TEXT,
                  PRIMARY KEY (username))''')
    
    # Potential connections table
    c.execute('''CREATE TABLE IF NOT EXISTS potential_connections
                 (username TEXT,
                  connections_data TEXT,
                  PRIMARY KEY (username))''')
    
    conn.commit()
    conn.close()

# Add functions to save and retrieve Reddit credentials
def save_reddit_credentials(username, reddit_username, reddit_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO reddit_credentials VALUES (?, ?, ?)', 
              (username, reddit_username, reddit_password))
    conn.commit()
    conn.close()

def get_reddit_credentials(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM reddit_credentials WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'reddit_username': result[1],
            'reddit_password': result[2]
        }
    return None

# Add functions to save and retrieve Reddit subscriptions
def save_reddit_subscriptions(username, subscriptions):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO reddit_subscriptions VALUES (?, ?)', 
              (username, json.dumps(subscriptions)))
    conn.commit()
    conn.close()

def get_reddit_subscriptions(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT subscriptions_data FROM reddit_subscriptions WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        # Convert JSON string back to list
        return json.loads(result[0])
    return []

def verify_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
    result = c.fetchone()
    conn.close()
    return bool(result)

def save_user(username, password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?, ?)', (username, password))
    conn.commit()
    conn.close()

def save_bluesky_credentials(username, bluesky_username, bluesky_password):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO bluesky_credentials VALUES (?, ?, ?)', 
              (username, bluesky_username, bluesky_password))
    conn.commit()
    conn.close()

def get_bluesky_credentials(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT bluesky_username, bluesky_password FROM bluesky_credentials WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'bluesky_username': result[0],
            'bluesky_password': result[1]
        }
    return None

def save_following_data(username, following_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Convert list to JSON string for storage
    following_json = json.dumps(following_data)
    c.execute('INSERT OR REPLACE INTO following_data VALUES (?, ?)', 
              (username, following_json))
    conn.commit()
    conn.close()

def get_following_data(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT following_data FROM following_data WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        # Convert JSON string back to list
        return json.loads(result[0])
    return []

def save_potential_connections(username, connections_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Convert list to JSON string for storage
    connections_json = json.dumps(connections_data)
    c.execute('INSERT OR REPLACE INTO potential_connections VALUES (?, ?)', 
              (username, connections_json))
    conn.commit()
    conn.close()

def get_potential_connections(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT connections_data FROM potential_connections WHERE username=?', (username,))
    result = c.fetchone()
    conn.close()
    
    if result and result[0]:
        # Convert JSON string back to list
        return json.loads(result[0])
    return []