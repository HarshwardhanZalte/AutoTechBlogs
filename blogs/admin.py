from django.contrib import admin
from .models import Blog, Comment

@admin.register(Blog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'created_at', 'source_url')
    search_fields = ('title', 'content')
    list_filter = ('author', 'created_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'blog_title', 'message', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'message')

    def blog_title(self, obj):
        return obj.blog.title
    blog_title.short_description = 'Blog Title'