from rest_framework import serializers
from .models import Blog, Comment

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'blog', 'name', 'message', 'created_at']

class BlogListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for the blog list view (home page).
    """
    class Meta:
        model = Blog
        fields = ['id', 'title', 'summary', 'image_url', 'author', 'created_at']

class BlogDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for the blog detail view, including comments.
    """
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Blog
        fields = [
            'id', 'title', 'summary', 'content', 'image_url', 'source_url',
            'author', 'tags', 'key_takeaways', 'discussion_questions',
            'created_at', 'comments'
        ]