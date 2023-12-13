from django.db import DatabaseError
from django import forms
from itertools import islice
from rest_framework import serializers

from ..models.questions import Question
from ..models.tags import Tag
from ..serializers.answers import AnswerSerializer
from ..serializers.tags import TagSerializer
from ..serializers.users import UserSerializer


class QuestionSerializer(serializers.ModelSerializer, forms.ModelForm): 
    answers = AnswerSerializer(many=True, required=False, read_only=True)
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ('author', 'title', 'tags', 'votes', 'answers', 'created_date')
    
    def get_cleaned_tags(self):
        tags = self.cleaned_data.get('tags')
        if not tags:
            return []
        else:
            tags = tags.replace(', ', ',').split(',')[:3]
            return list(set(tags))
        
    def get_new_tags(self, tagslist):
        return [tag for tag in tagslist
                if tag not in
                [c.__str__ for c in Tag.objects.all()]]
        
    @property
    def upd_tags(self):
        tags_list = self.get_cleaned_tags()
        new_tags = self.get_new_tags(tags_list)
        batch = list(
                     islice(
                            (Tag(content=tag) for tag in new_tags), len(new_tags)
                             )
                    )
        try:
            Tag.objects.bulk_create(batch, len(new_tags))
        except DatabaseError:
            pass

        tags = Tag.objects.filter(content__in=tags_list).all()
        upd_data = self.cleaned_data.copy()
        upd_data['tags'] = tags
        upd_data.pop('csrfmiddlewaretoken')
        return upd_data
