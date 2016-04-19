from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.views.generic import View
from .forms import UserForm, UserLogin
from django.views import generic
from .models import Account
from django.contrib.auth.models import User
import locale
import account_type


def fetch_user_context(user):
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
            debit_activated = user_account.card_activated
            debit_pin = user_account.card_pin
        except:
            checking_text = '$0'
            debit_activated = False
            debit_pin = ''

        try:
            user_account = Account.objects.get(user_id=user.id, account_type=account_type.credit)
            credit_text = locale.currency(user_account.balance, grouping=True)
            credit_exists = True
            credit_pin = user_account.card_pin
        except:
            credit_text = '$0'
            credit_exists = False
            credit_pin = ''

    context = {'savings_text': savings_text, 'checking_text': checking_text, 'credit_text': credit_text, 'credit_exists': credit_exists, 'debit_activated': debit_activated, 'credit_pin': credit_pin, 'debit_pin': debit_pin}
    return context

class IndexView(View):
    template_name = 'main/index.html'
    form_class = UserLogin

    def get(self, request):
        context = fetch_user_context(request.user)

        return render(request, self.template_name, context)

    def post(self, request):
        user = None

        if request.user.is_authenticated():
            try:
                pin = request.POST['pin']
                credit_acct = Account()
                credit_acct.user = request.user
                credit_acct.account_type = account_type.credit
                credit_acct.card_pin = pin
                credit_acct.card_activated = True
                credit_acct.card_num = credit_acct.generate_card()
                credit_acct.save()

                context = fetch_user_context(request.user)

                context['card_num'] = credit_acct.card_num
                context['card_created'] = True
                context['card_type'] = 'credit'

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
                context.update(fetch_user_context(request.user))

                return render(request, self.template_name, context)
            except:
                pass

            try:
                context = {}

                current_user = request.user
                current_user.email = request.POST['email']

                debit_acct = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
                debit_acct.card_pin = str(request.POST['debit_pin'])

                if 'activate_debit' in request.POST:
                    debit_acct.card_num = debit_acct.generate_card()
                    debit_acct.card_activated = True
		    context['card_created'] = True
                    context['card_type'] = 'debit'
                    context['card_num'] = debit_acct.card_num

                debit_acct.save()

                if 'credit_pin' in request.POST:
                    credit_acct = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
                    credit_acct.card_pin = str(request.POST['credit_pin'])
                    credit_acct.save()

                if request.POST['password'] != '':
                    current_user.set_password(request.POST['password'])

                current_user.save()

                context.update(fetch_user_context(request.user))

                return render(request, self.template_name, context)
            except:
                pass

            try:
                spend_amount = int(request.POST['spend_amount'])
		card_number = request.POST['card_number']
	        card_pinumber = request.POST['card_pin']

		acct = Account.objects.get(user_id=request.user.id, card_num=card_number, card_pin=card_pinumber)
		
		if acct.account_type == account_type.checking:
		    acct.balance -= spend_amount
		elif acct.account_type == account_type.credit:
		    acct.balance += spend_amount

		acct.save()

		return render(request, self.template_name, fetch_user_context(request.user))
	    except:
		pass

	    try:
		deposit_amount = int(request.POST['deposit_amount'])
		deposit_account = request.POST['deposit_account']

		acct = Account.objects.get(user_id=request.user.id, account_type=deposit_account)
		acct.balance += deposit_amount
		acct.save()

		return render(request, self.template_name, fetch_user_context(request.user))
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
        context = request.session.pop('context', False)

	if not context:
            context = fetch_user_context(request.user)

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
        context = request.session.pop('context', False)

	if not context:
            context = fetch_user_context(request.user)

        return render(request, self.template_name, context)

    def post(self, request,pk, id):
        context = fetch_user_context(request.user)
        context['transfer_fail'] = False

        amount = request.POST['amount']
        username = request.POST['username']
        amount = int(amount)

        if id == '0':
            saving_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)

            if amount > saving_account.balance:
                context['transfer_fail'] = True
	    else:
                saving_account.balance = saving_account.balance - amount
                saving_account.save()
        else:
            checking_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)
            
	    if amount > checking_account.balance:
		context['transfer_fail'] = True
	    else:
                checking_account.balance = checking_account.balance - amount
                checking_account.save()

        if not context['transfer_fail']:
            user = User.objects.get(username = username)
            account = Account.objects.get(user = user, account_type=account_type.checking)
            account.balance += amount
            account.save()

        request.session['context'] = context

        return redirect('main:detail', pk)


class TransferBetweenView(View):
    template_name = 'main/transfer_between.html'

    def get(self, request, pk, id):
        context = request.session.pop('context', False)

	if not context:
            context = fetch_user_context(request.user)

	if id == '0':
            context['transfer_type'] = "Savings"
	else:
	    context['transfer_type'] = "Checking"

        return render(request, self.template_name, context)

    def post(self, request, pk, id):
        context = fetch_user_context(request.user)

        amount = request.POST['amount']
        amount = int(amount)

        saving_account = Account.objects.get(user_id=request.user.id, account_type=account_type.savings)
        checking_account = Account.objects.get(user_id=request.user.id, account_type=account_type.checking)

        if id == '0':
	    if amount > saving_account.balance:
	        context['transfer_fail'] = True
	    else:
                saving_account.balance = saving_account.balance - amount
                checking_account.balance = checking_account.balance + amount
        else:
	    if amount > checking_account.balance:
	        context['transfer_fail'] = True
	    else:
                checking_account.balance = checking_account.balance - amount
                saving_account.balance = saving_account.balance + amount

        saving_account.save()
        checking_account.save()

        request.session['context'] = context

        return redirect('main:detail', pk)

