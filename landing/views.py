from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout 
from .forms import UserCreationForm, LoginForm, SignupForm
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def index (request):
  
    return render(request, 'landing/main.html')


# signup page
def user_signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('landing:login')
    else:
        form = SignupForm()
    return render(request, 'landing/signup.html', {'form': form})

# login page
def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)    
                return redirect('landing:index')
    else:
        form = LoginForm()
    return render(request, 'landing/login.html', {'form': form})

# logout page
@login_required
def user_logout(request):
    logout(request)
    return redirect('landing:login')
