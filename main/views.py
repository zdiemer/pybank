from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import UserForm, UserLogin
from django.views import generic
from .models import Account
from django.contrib.auth.models import User
import locale
import account_type


class IndexView(View):
    template_name = 'main/index.html'
    form_class = UserLogin

    savings_text = '$0'
    checking_text = '$0'
    credit_text = '$0'
    credit_exists = False

    def fetch_user_context(self, user):
        if user.is_authenticated:
            locale.setlocale(locale.LC_ALL, '')
            try:
                user_account = Account.objects.get(user_id=user.id, account_type=account_type.savings)
                savings_text = locale.currency(user_account.balance, grouping=True)
            except:
                savings_text = '$0'

            try:
                user_account = Account.objects.get(user_id=user.id, account_type=account_type.checking)
                checking_text = locale.currency(user_account.balance, grouping=True)
            except:
                checking_text = '$0'

            try:
                user_account = Account.objects.get(user_id=user.id, account_type=account_type.credit)
                credit_text = locale.currency(user_account.balance, grouping=True)
                credit_exists = True
            except:
                credit_text = '$0'
                credit_exists = False

        context = {'savings_text': savings_text, 'checking_text': checking_text, 'credit_text': credit_text, 'credit_exists': credit_exists}
        return context

    def get(self, request):
        context = self.fetch_user_context(request.user)

        return render(request, self.template_name, context)

    def post(self, request):
        user = None

        if request.user.is_authenticated():
            print request.user
            try:
                pin = request.POST['pin']
                credit_acct = Account()
                credit_acct.user = request.user
                credit_acct.account_type = account_type.credit
                credit_acct.card_pin = pin
                credit_acct.card_activated = True
                credit_acct.card_num = credit_acct.generate_card()
                credit_acct.save()

                context = self.fetch_user_context(request.user)

                context['card_num'] = credit_acct.card_num
                context['card_created'] = True

                return render(request, self.template_name, context)
            except:
                pass

            try:
                payment_result = True
                overpayment = False
                new_balance = ''

                amount = int(request.POST['amount'])
                account = request.POST['account']

                fetched_acct = Account.objects.get(user_id=request.user.id, account_type=account)
                credit_acct = Account.objects.get(user_id=request.user.id, account_type=account_type.credit)

                current_balance = fetched_acct.balance

                context = {}
                context['paying_card'] = True

                if current_balance < amount:
                    payment_result = False
                elif amount > credit_acct.balance:
                    payment_result = False
                    overpayment = True
                else:
                    locale.setlocale(locale.LC_ALL, '')
                    fetched_acct.balance = current_balance - amount
                    fetched_acct.save()

                    new_balance = locale.currency(credit_acct.balance - amount, grouping=True)

                    credit_acct.balance = credit_acct.balance - amount
                    credit_acct.save()

                context['payment_result'] = payment_result
                context['overpayment'] = overpayment
                context['new_balance'] = new_balance
                context.update(self.fetch_user_context(request.user))

                return render(request, self.template_name, context)
            except:
                pass
        else:
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request,user)
                return redirect('main:index')

        return render(request, self.template_name, {"user":user})


class DetailView(View):
    template_name = 'main/transfer.html'

    def get(self, request, pk):
        saving_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
        checking_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)

        context = {'savings':saving_account , 'checking': checking_account}
        return render(request, self.template_name,context)

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
            checking_acct.card_num = checking_acct.generate_card()
            checking_acct.account_type = account_type.checking
            checking_acct.save()

            user = authenticate(username = username, password = password)

            if user is not None:
                    login(request,user)
                    return redirect('main:index')

        return render(request, 'main/index.html', {'form':form})


class TransferView(View):
    template_name = 'main/transfer_process.html'

    def get(self, request, pk, id):
        return render(request, self.template_name)

    def post(self, request,pk, id):
        amount = request.POST['amount']
        username = request.POST['username']
        amount = int(amount)
        #get current account
        if id == '0':
            saving_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
            # do error checking...
            saving_account.balance = saving_account.balance - amount
            saving_account.save()
        else:
            checking_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
            #do error checking...
            checking_account.balance = checking_account.balance - amount
            checking_account.save()

        user = User.objects.get(username = username)
        account = Account.objects.get(user = user, account_type=account_type.savings)
        account.balance += amount
        account.save()
        return redirect('main:detail',pk)


class TransferBetweenView(View):
    template_name = 'main/transfer_between.html'

    def get(self, request, pk, id):
        return render(request, self.template_name)

    def post(self, request, pk, id):
        amount = request.POST['amount']
        amount = int(amount)
        saving_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
        checking_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
        if id == '0':
            saving_account.balance = saving_account.balance - amount
            checking_account.balance = checking_account.balance + amount
        else:
            checking_account.balance = checking_account.balance - amount
            saving_account.balance = saving_account.balance + amount

        saving_account.save()
        checking_account.save()
        return redirect('main:detail', pk)

