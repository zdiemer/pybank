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
    credit_text = '$0'
    credit_exists = False

    def get(self, request):
        if request.user.is_authenticated:
            locale.setlocale(locale.LC_ALL, '')
            try:
                user_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
                savings_text = locale.currency(user_account.balance, grouping=True)
            except:
                savings_text = '$0'

            try:
                user_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
                checking_text = locale.currency(user_account.balance, grouping=True)
            except:
                checking_text = '$0'

            try:
                user_account = Account.objects.get(user_id=request.user.id, account_type=account_type.credit)
                credit_text = locale.currency(user_account.balance, grouping=True)
                credit_exists = True
            except:
                credit_text = '$0'
                credit_exists = False

        context = {'savings_text': savings_text, 'checking_text': checking_text, 'credit_text': credit_text, 'credit_exists': credit_exists}

        return render(request, self.template_name, context)

    def post(self, request):
        if request.user.is_authenticated:
            pin = ''
            try:
		print "trying to get pin"
                pin = request.POST['pin']
		print "got pin", pin
                credit_acct = Account()
                credit_acct.user = request.user
                credit_acct.account_type = account_type.credit
                credit_acct.card_pin = pin
                credit_acct.save()
		print "saving"

                context = {'card_num': credit_acct.card_num, 'card_created': True}

                print "Saved credit card with pin", pin
                return render(request, self.template_name, context)
            except:
		print "error"
                pin = ''
        else:
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
            savings_acct = Account()
            savings_acct.user = user
            savings_acct.account_type = account_type.savings
            savings_acct.save()

            # create savings account
            checking_acct = Account()
            checking_acct.user = user
            checking_acct.account_type = account_type.checking
            checking_acct.save()

            user = authenticate(username = username, password = password)

            if user is not None:
                    login(request,user)
                    return redirect('main:index')

        return render(request, 'main/index.html', {'form':form})


class TranferView(View):
    template_name = 'main/transfer.html'

    def get(self, request):
        return render(request, self.template_name)
