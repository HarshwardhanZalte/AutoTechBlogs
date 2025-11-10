from django.urls import path
from . import views

app_name = 'blogs'

urlpatterns = [
    # --- Template Views ---
    path('', views.home_view, name='home'),
    path('blog/<int:pk>/', views.blog_detail_view, name='blog_detail'),

    # --- API Views ---
    path('api/generate/', views.GenerateBlogsAPI.as_view(), name='api_generate'),
    path('api/blogs/', views.BlogListAPI.as_view(), name='api_blog_list'),
    path('api/blogs/<int:pk>/', views.BlogDetailAPI.as_view(), name='api_blog_detail'),
    path('api/comments/', views.CommentCreateAPI.as_view(), name='api_comment_create'),
]