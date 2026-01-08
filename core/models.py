from django.db import models
from django.utils import timezone
class Todo(models.Model):
    title = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
