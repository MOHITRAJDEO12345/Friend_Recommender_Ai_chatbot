from atproto import Client

def get_following_list(client):
    try:
        # Get the user's DID (Decentralized Identifier)
        profile = client.get_profile(client.me.did)
        # Fetch following list
        following = client.get_follows(actor=profile.did)
        
        # Return the following list for further processing
        return following.follows
    except Exception as e:
        print(f"Error fetching following list: {e}")
        return []

# Function to get posts from a user to analyze interests
def get_user_posts(client, user_did, limit=10):
    try:
        posts = client.get_author_feed(actor=user_did, limit=limit)
        return posts.feed
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

# Function to get followers of someone you follow
def get_followers_of_following(client, user_did, limit=50):
    try:
        followers = client.get_followers(actor=user_did, limit=limit)
        return followers.followers
    except Exception as e:
        print(f"Error fetching followers: {e}")
        return []

def main():
    try:
        client = Client()
        client.login('mohitrajdeo16deoghar@gmail.com', 'M@hit12345')
        get_following_list(client)
    except Exception as e:
        print(f"Error logging in: {e}")

if __name__ == '__main__':
    main()