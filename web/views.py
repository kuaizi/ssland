#!/usr/bin/env python
# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import forms as auth_forms
from django.contrib.auth.decorators import login_required
from web.models import ProxyAccount, Quota

from core.util import encodeURIComponent, get_prev_uri
import pyqrcode, io

def FlickBackResponse(request):
    prevURL = get_prev_uri(request)
    return redirect(prevURL)

def qr_view(request):
    qr = pyqrcode.create(request.GET['data'])
    out = io.BytesIO()
    qr.svg(out, scale=5)
    return HttpResponse(
        out.getvalue(),
        content_type = 'image/svg+xml'
    )

def login_view(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
    except:
        return render(request, 'login.html', {
            'title': 'Login',
            'nexturi': request.GET['next'] if ('next' in request.GET) else '/',
        })
    if user is not None:
        login(request, user)
        return redirect(request.POST['next'])
    else:
        return render(request, 'login.html', {
            'title': 'Login', 
            'nexturi': request.POST['next'],
            'username': username, 
        })

def logout_view(request):
    logout(request)
    return redirect('/')

def index_view(request):
    return render(request, 'index.html')

@login_required
def passwd_view(request):
    u = request.user
    prevURL = get_prev_uri(request)

    if request.method == "POST":
        form = auth_forms.PasswordChangeForm(u, request.POST)
        if form.is_valid():
            form.save()
            return redirect(prevURL)
    else:
        form = auth_forms.PasswordChangeForm(u)
    
    return render(request, 'user.edit.html', {
        'title': 'Edit Password',
        'prev': prevURL,
        'form': form,
    })

@login_required
def account_view(request):
    user = request.user
    accounts = ProxyAccount.objects.filter(user = user)
    return render(request, 'account.html', {'title': 'Accounts', 'accounts': accounts})

@login_required
def account_edit_view(request, service):
    user = request.user
    account = ProxyAccount.objects.filter(user=user,service=service) [0]
    UserForm = account.form

    quotas = []
    for quota in Quota.objects.filter(account=account):
        quota.update_from_alias()
        if not quota.is_really_enabled: continue
        quotas.append({
            'id': quota.pk,
            'name': quota.name,
            'desc': quota.descript(),
            'enabled': True,
            'o': quota,
        })

    if request.method == "POST":
        form = UserForm(request.POST)
        bypass_twostep_validate = not (getattr(form, 'is_valid_for_account', None) and True)
        if form.is_valid() and (bypass_twostep_validate or form.is_valid_for_account(account)):
            account.config.update(form.cleaned_data)
            account.save()
            return redirect('/account/#' + encodeURIComponent(service))
    else:
        form = UserForm(initial=account.config)
            
    return render(request, 'account.edit.html', {
        'title': 'Edit Account', 
        'account': account,
        'prev': '/account/#' + encodeURIComponent(service),
        'form': form,
        'quotas': quotas,
    })

from web import views_admin
