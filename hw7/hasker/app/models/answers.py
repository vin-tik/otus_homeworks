from django.conf import settings
from django.db import models

from .questions import Question

class Answer(models.Model):
    answer = models.ForeignKey(Question, on_delete=models.PROTECT,
                                         related_name='answers',
                                         default=None,
                                         blank=False)
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               related_name='answers',
                               on_delete=models.CASCADE)
    
    votes = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                   blank=True,
                                   related_name='answers')
    
    flag = models.BooleanField(default=None, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['question', 'author'], name='answers')]
        
    def __str__(self):
        return self.answer
