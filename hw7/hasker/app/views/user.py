from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework import mixins, viewsets
# from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from app.forms.users import CustomUserCreationForm
from app.models.users import User
from app.serializers.users import UserSerializer


class NewUserCreateView(mixins.CreateModelMixin,
                        viewsets.GenericViewSet):
    model = User
    template_name = "new_user.html"
    serializer_class = UserSerializer
    # renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        form = CustomUserCreationForm()
        return Response({'form': form})

    def create(self, request, *args, **kwargs):
        form = CustomUserCreationForm(data=request.data, files=request.FILES)
        if form.is_valid():
            new_user = form.save(commit=True)
            login(request, new_user)
            return redirect('/ask')
        return JsonResponse(form.errors)
