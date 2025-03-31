import google.generativeai as genai

def setup_gemini(api_key, temperature=0.7):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash', 
                                generation_config={"temperature": temperature})

def analyze_interests(model, posts_data):
    prompt = f"""Extract TOP 3-5 main interests from these posts. 
Format as numbered list with emoji prefixes. Max 10 words per interest.

Posts:
{posts_data}

Respond ONLY with the formatted list, nothing else."""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "1. 📱 Technology\n2. 💻 Programming\n3. 🤖 AI and Machine Learning"

def suggest_connections(model, my_interests, potential_connections_data):
    prompt = f"""
    Based on the following interests:
    {my_interests}
    
    And these potential connections:
    {potential_connections_data}
    
    Suggest 5 people who would be good connections based on shared interests or complementary topics.
    For each suggestion, explain why they would be a good connection.
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "Could not generate suggestions at this time."