from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages

def register_user_form(request):
    if request.method == "POST":
        create_user = UserCreationForm(request.POST)
        if create_user.is_valid():
            create_user.save()
            messages.success(request, "Conta criada com sucesso! Você já pode fazer login.")
            return redirect("login")
    else:
        create_user = UserCreationForm()

    return render(request, 'register.html', {'create_user': create_user})


def login(request):
    if request.method == "POST":
        login_form = AuthenticationForm(request, data=request.POST)
        if login_form.is_valid():
            user = login_form.get_user()
            auth_login(request, user)
            return redirect("workspace")
        else:
            messages.error(request, "Usuário ou senha incorretos.")
    else:
        login_form = AuthenticationForm()

    return render(request, "login.html", {"login_form": login_form})
