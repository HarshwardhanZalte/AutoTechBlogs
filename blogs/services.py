import requests
import google.generativeai as genai
import json
import os
from django.conf import settings
from .models import Blog
import logging

# Set up logging
logger = logging.getLogger(__name__)

def fetch_gnews_articles():
    """
    Fetches trending technology articles from the GNews.io API.
    """
    api_key = settings.GNEWS_API_KEY
    if not api_key:
        logger.error("GNEWS_API_KEY not found in settings.")
        return []

    url = f"https://gnews.io/api/v4/top-headlines?topic=technology&lang=en&max=3&apikey={api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status() # Raise an exception for bad status codes
        data = response.json()
        articles = data.get('articles', [])
        logger.info(f"Fetched {len(articles)} articles from GNews.")
        return articles
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching GNews articles: {e}")
        return []

def generate_blog_from_article(article):
    """
    Uses the Gemini API to generate a blog post from a news article.
    """
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.error("GEMINI_API_KEY not found in settings.")
        return None

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        logger.error(f"Error configuring Gemini API: {e}")
        return None

    # This is the JSON schema the AI must follow
    response_schema = {
        "type": "OBJECT",
        "properties": {
            "blogTitle": {"type": "STRING"},
            "blogSummary": {"type": "STRING"},
            "blogContent": {"type": "STRING"},
            "originalSourceUrl": {"type": "STRING"},
            "imageUrl": {"type": "STRING"},
            "tags": {"type": "STRING"},
            "keyTakeaways": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            },
            "discussionQuestions": {
                "type": "ARRAY",
                "items": {"type": "STRING"}
            }
        },
        "required": [
            "blogTitle", "blogSummary", "blogContent", "originalSourceUrl",
            "imageUrl", "tags", "keyTakeaways", "discussionQuestions"
        ]
    }

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": response_schema
    }

    # Note: We are using a specific model preview that supports JSON mode.
    # Update this model as new versions are released.
    model = genai.GenerativeModel(
        "gemini-2.5-flash-preview-09-2025",
        generation_config=generation_config
    )

    system_prompt = """
    You are an expert tech blogger. Your tone is engaging, insightful, and easy to understand.
    Your task is to write an interactive and engaging blog post based on the provided news article.
    
    RULES:
    - Do NOT just copy the article.
    - Use the article's title, description, and content as a source of facts.
    - Write an original piece in your own voice in English only.
    - Create a new, catchy title for the blog post.
    - Language must be easy to understand.
    - Structure the content with clear sections:
        * Start with an engaging introduction
        * Break down key points into sections with <h2> subheadings
        * Use <h3> for any nested subsections
        * Include a "Quick Takeaways" section (which you'll also put in the JSON)
        * End with a "Why This Matters" section
    - Format requirements for 'blogContent' HTML:
        * Use <h2> for main sections
        * Use <h3> for subsections
        * Use <p> tags for paragraphs. Add a blank line between paragraphs.
        * Use <blockquote> for important quotes or highlights
        * Use <ul> and <li> for bullet points
        * Include a <table> if relevant data is available
    - Add interactive elements to 'blogContent':
        * Include a "Key Points" summary box using a <div> with class 'key-points-box'.
        * Add a "Did You Know?" fact box using a <div> with class 'did-you-know-box'.
        * Include thought-provoking questions for readers at the end of the post (which you'll also put in the JSON).
    - The output MUST be in the provided JSON format.
    - The 'blogSummary' should be a concise one or two-sentence summary of the new post.
    """

    user_prompt = f"""
    Please write a blog post based on this article:
    - Title: {article.get('title', 'N/A')}
    - Description: {article.get('description', 'N/A')}
    - Content: {article.get('content', 'N/A')}
    - Source URL: {article.get('url', '')}
    - Image URL: {article.get('image', '')}
    """

    try:
        # We send both system and user prompts as a list
        response = model.generate_content([system_prompt, user_prompt])
        
        # Extract the JSON text and parse it
        json_text = response.text
        blog_data = json.loads(json_text)
        
        logger.info(f"Successfully generated blog for: {article.get('title')}")
        return blog_data
        
    except Exception as e:
        logger.error(f"Error generating content with Gemini: {e}")
        # Log the full response if it's not a JSON parsing error
        if 'response' in locals():
            logger.error(f"Gemini raw response: {response.parts}")
        return None

def run_blog_generation_pipeline():
    """
    Main pipeline function. Fetches articles, generates blogs, and saves to DB.
    """
    logger.info("Starting blog generation pipeline...")
    articles = fetch_gnews_articles()
    if not articles:
        logger.warning("No articles fetched. Pipeline ending.")
        return {"status": "no_articles", "new_blogs": 0}
    print(articles)
    new_blogs_count = 0
    for article in articles:
        source_url = article.get('url')
        if not source_url:
            logger.warning("Skipping article with no source URL.")
            continue
        
        # skip blogs without images
        if not article.get('image'):
            logger.warning("Skipping article without an image.")
            continue
        
        # 1. Check if blog post with this source URL already exists
        if Blog.objects.filter(source_url=source_url).exists():
            logger.info(f"Skipping already existing article: {source_url}")
            continue

        # 2. Generate blog content
        blog_data = generate_blog_from_article(article)

        if not blog_data:
            logger.error(f"Failed to generate blog data for: {source_url}")
            continue

        # 3. Save the new blog post to the database
        try:
            Blog.objects.create(
                title=blog_data.get('blogTitle'),
                summary=blog_data.get('blogSummary'),
                content=blog_data.get('blogContent'),
                image_url=blog_data.get('imageUrl'),
                source_url=blog_data.get('originalSourceUrl'),
                tags=blog_data.get('tags'),
                key_takeaways=blog_data.get('keyTakeaways'),
                discussion_questions=blog_data.get('discussionQuestions'),
                author="AI Author"
            )
            new_blogs_count += 1
            logger.info(f"Successfully created blog: {blog_data.get('blogTitle')}")
        except Exception as e:
            logger.error(f"Error saving blog to database: {e}")
    
    logger.info(f"Blog generation pipeline finished. Added {new_blogs_count} new blogs.")
    return {"status": "success", "new_blogs": new_blogs_count}