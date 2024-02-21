from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, authenticate, login
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse_lazy
from django.views import generic

from .forms import LoginForm  # Import your login form

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from allauth.socialaccount.models import SocialAccount


def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('welcome')
    return render(request, 'users/login.html')

def redirect_to_welcome(user):
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        return redirect('welcome')  # Redirect to welcome page if authenticated via Google
    else:
        return redirect('home')  # Redirect to home page if authenticated via other means


def welcome_view(request):
    if request.user.is_authenticated:
        return render(request, 'welcome.html', {'user': request.user})
    return redirect('home')  # Redirect to login page if not authenticated

def logout(request):
    auth_logout(request)
    return redirect('/')



class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")  # Make sure "login" matches your URL name
    template_name = "users/signup.html"
