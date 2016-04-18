from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import UserForm, UserLogin
from django.views import generic
from .models import Account
import locale

class IndexView(View):
    template_name = 'main/index.html'
    form_class = UserLogin
    savings_text = '$0'
    checking_text = '$0'

    def get(self, request):
        if request.user.is_authenticated:
            try:
                user_account = Account.objects.get(user_id=request.user.id)
                locale.setlocale(locale.LC_ALL, '')
                savings_text = locale.currency(user_account.saving_balance, grouping=True)
                checking_text = locale.currency(user_account.checking_balance, grouping=True)
            except:
                savings_text = '$0'
                checking_text = '$0'

        context = {'savings_text': savings_text, 'checking_text': checking_text}

        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return render(request, 'main/index.html')

        return render(request, self.template_name, {'form':form})


class DetailView(generic.DetailView):
    model = Account
    template_name = 'main/detail.html'

class UserFormView(View):
    form_class = UserForm
    template_name = 'main/registration_form.html'

    def get(self, request):
        form = self.form_class(None)
        return render(request, self.template_name, {'form':form})

    def post(self, request):

        form = self.form_class(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            # cleaned data
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            account = Account()
            account.user = user
            account.save()

            user = authenticate(username = username, password = password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect('main:index')

        return render(request, 'main/index.html', {'form':form})
