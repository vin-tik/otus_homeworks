from django.db import models

class Tag(models.Model):
    tag = models.TextField(null=False, max_length=20, unique=True)

    def __str__(self):
        return self.tag
