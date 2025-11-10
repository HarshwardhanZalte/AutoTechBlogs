from django.db import models

class Blog(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField()
    content = models.TextField() # This will store the generated HTML
    image_url = models.URLField(max_length=1024, blank=True, null=True)
    source_url = models.URLField(max_length=1024, unique=True)
    author = models.CharField(max_length=100, default="AI Author")
    tags = models.CharField(max_length=255, blank=True, null=True)
    key_takeaways = models.JSONField(null=True, blank=True)
    discussion_questions = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class Comment(models.Model):
    blog = models.ForeignKey(Blog, related_name='comments', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Comment by {self.name} on {self.blog.title}'