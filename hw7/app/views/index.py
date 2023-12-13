from django.contrib.auth import get_user
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.response import Response

from ..models.questions import Question
from ..serializers.question import QuestionSerializer


class IndexView(mixins.ListModelMixin,
                viewsets.GenericViewSet):

    model = Question
    template_name = 'index.html'
    serializer_class = QuestionSerializer
    queryset = Question.objects.all().order_by('-created_date')

    def get_idx_queryset(self, request):
        user = get_user(request)

        top_questions = Question.objects.all().order_by('-rating', '-created_date')
        q = top_questions.annotate(votes_count=Count('votes'))
        trending = q.order_by('-total_votes', '-created_at')[:10]
        paginator = Paginator(self.queryset, 20)
 
        top_paginator = Paginator(trending, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        top_page_obj = top_paginator.get_page(page_number)

        return Response({'questions': self.queryset,
                         'trending': trending,
                         'top_questions': top_questions,
                         'page_obj': page_obj,
                         'from_date': timezone.now(),
                         'top_page_obj': top_page_obj,
                         'user': user})
