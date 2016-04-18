from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import UserForm, UserLogin
from django.views import generic
from .models import Account
import locale
import account_type


class IndexView(View):
    template_name = 'main/index.html'
    form_class = UserLogin
    savings_text = '$0'
    checking_text = '$0'

    def get(self, request):
        if request.user.is_authenticated:
            locale.setlocale(locale.LC_ALL, '')
            try:
                user_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
                savings_text = locale.currency(user_account.saving_balance, grouping=True)
            except:
                savings_text = '$0'

            try:
                user_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
                checking_text = locale.currency(user_account.checking_balance, grouping=True)
            except:
                checking_text = '$0'

        context = {'savings_text': savings_text, 'checking_text': checking_text}

        return render(request, self.template_name, context)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request,user)
            return redirect('main:index')

        return render(request, self.template_name,)


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

            # create savings account
            account = Account()
            account.user = user
            account.account_type = account_type.savings
            account.save()

            # create savings account
            account = Account()
            account.user = user
            account.account_type = account_type.checking
            account.save()

            user = authenticate(username = username, password = password)

            if user is not None:
                    login(request,user)
                    return redirect('main:index')

        return render(request, 'main/index.html', {'form':form})


class TranferView(View):
    template_name = 'main/transfer.html'

    def get(self, request):
        return render(request, self.template_name)
