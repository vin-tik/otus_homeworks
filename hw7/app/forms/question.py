from django import forms
import re

from ..models.questions import Question


def tags_validation(inp):
    if not re.match(r'^\w*[,?\s?\w+]+$', inp):
        raise forms.ValidationError("Разделите теги запятой")


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('title', 'content', 'tags')
        widgets = {
            'title': forms.TextInput(
                attrs={'class': 'form-control-sm', 'placeholder': "Enter title"}),
            'content': forms.Textarea(attrs={
                'class': 'form-control-sm', 'placeholder': "Enter text a question"}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control-sm', 'placeholder': "Enter tags with ,"})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tags'].validators = [tags_validation]
        self.fields['tags'].help_text = "Разделите теги запятой"

