from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import mixins, status, viewsets
# from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response

from app.models.users import User
from app.serializers.users import UserSerializer


class UserLoginView(mixins.CreateModelMixin,
                    viewsets.GenericViewSet):
    model = User
    template_name = "login.html"
    serializer_class = UserSerializer
    # renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        form = AuthenticationForm()
        return Response({'form': form})

    def create(self, request, *args, **kwargs):
        form = AuthenticationForm(data=request.data)
        if form.is_valid():
            user = authenticate(
                request,
                username=request.data['username'],
                password=request.data['password']
            )
            if user:
                login(request, user)
                return redirect('/ask')
        return HttpResponse(status=status.HTTP_401_UNAUTHORIZED)
