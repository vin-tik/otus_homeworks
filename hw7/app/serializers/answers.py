from django import forms
from rest_framework import serializers
from ..models.answers import Answer

class AnswerSerializer(serializers.ModelSerializer):
    content = forms.CharField(label='', widget=forms.Textarea, required=True)
    class Meta:
        model = Answer
        fields = ('author', 'content', 'votes', 'question', 'created_date')
