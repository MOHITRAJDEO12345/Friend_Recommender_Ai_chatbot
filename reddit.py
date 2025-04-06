import praw

def get_reddit_client(username, password):
    """
    Initialize and return a Reddit client using the provided credentials
    """
    try:
        reddit = praw.Reddit(
            client_id='Jg7fMWffCP-SRz2w4ySkNg',
            client_secret='96iDg9AUiXhqjIIP1ucTNVcEjatTOg',
            username=username,
            password=password,
            user_agent='python:friend-recommender:v1.0 (by /u/Msmskjsnsnssnnsjwkdj)'
        )
        return reddit
    except Exception as e:
        print(f"Error initializing Reddit client: {e}")
        return None

def get_subscribed_subreddits(reddit_client, limit=100):
    """
    Get the list of subreddits the user is subscribed to
    """
    try:
        subscribed_subreddits = []
        for subreddit in reddit_client.user.subreddits(limit=limit):
            subscribed_subreddits.append({
                "name": subreddit.display_name,
                "url": f"https://www.reddit.com/r/{subreddit.display_name}",
                "subscribers": subreddit.subscribers,
                "description": subreddit.public_description[:100] + "..." if len(subreddit.public_description) > 100 else subreddit.public_description
            })
        return subscribed_subreddits
    except Exception as e:
        print(f"Error fetching subscribed subreddits: {e}")
        return []