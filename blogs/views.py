from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Blog, Comment
from .serializers import BlogListSerializer, BlogDetailSerializer, CommentSerializer
from .services import run_blog_generation_pipeline

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

# --- Template Views (Frontend) ---

def home_view(request):
    """
    Displays the home page with a paginated list of blog posts.
    """
    blog_list = Blog.objects.all().order_by('-created_at')
    paginator = Paginator(blog_list, 9) # 9 blogs per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj
    }
    return render(request, 'blogs/index.html', context)

def blog_detail_view(request, pk):
    """
    Displays the full blog post, its details, and comments.
    """
    blog = get_object_or_404(Blog, pk=pk)
    comments = blog.comments.all().order_by('-created_at')
    
    # Split tags for the template
    tags_list = []
    if blog.tags:
        tags_list = [tag.strip() for tag in blog.tags.split(',')]

    context = {
        'blog': blog,
        'comments': comments,
        'tags_list': tags_list
    }
    return render(request, 'blogs/blog_detail.html', context)


# --- API Views (Backend) ---

class GenerateBlogsAPI(APIView):
    """
    Triggers the blog generation pipeline.
    Accessible only by admin users.
    """
    # permission_classes = [IsAdminUser]

    def get(self, request, *args, **kwargs):
        """
        Handles the GET request to trigger the pipeline.
        """
        try:
            result = run_blog_generation_pipeline()
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class BlogListAPI(generics.ListAPIView):
    """
    API endpoint to list all blogs (lightweight version).
    """
    queryset = Blog.objects.all().order_by('-created_at')
    serializer_class = BlogListSerializer

class BlogDetailAPI(generics.RetrieveAPIView):
    """
    API endpoint to get a single blog's details.
    """
    queryset = Blog.objects.all()
    serializer_class = BlogDetailSerializer

class CommentCreateAPI(generics.CreateAPIView):
    """
    API endpoint to create a new comment.
    """
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        # Ensure the 'blog' instance is correctly associated.
        blog_id = self.request.data.get('blog')
        blog = get_object_or_404(Blog, id=blog_id)
        serializer.save(blog=blog)