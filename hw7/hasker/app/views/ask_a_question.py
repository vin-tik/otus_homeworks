from django.contrib.auth import get_user
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import mixins, viewsets
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from ..forms.question import QuestionForm
from ..models.questions import Question
from ..serializers.question import QuestionSerializer


class AskQuestionView(mixins.CreateModelMixin,
                      mixins.RetrieveModelMixin,
                      viewsets.GenericViewSet):
    model = Question
    template_name = "ask_question.html"
    serializer_class = QuestionSerializer
    # renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        user = get_user(request)
        form = QuestionForm()
        return Response({'form': form, 'user': user})

    def create(self, request, *args, **kwargs):
        user = get_user(request)
        form = QuestionForm(data=request.data)
        tags_list = form.cleaned_data['tags']

        if form.is_valid():
            serializer = QuestionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(author=user, tags=tags_list)
        else:
            return HttpResponse(form.errors)
        return redirect('/ask')
