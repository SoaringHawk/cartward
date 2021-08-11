from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ChangeEmail, ProfileUpdateForm, ProfileRegisterForm, UserLoginForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from users.models import Profile, Address, Order, Btcinvoice
from django.contrib.auth.models import User
from django.views import View
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.contrib.auth.forms import PasswordChangeForm
import json
import requests
from django.core.paginator import Paginator
import uuid
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.conf import settings


# Create your views here.

def home(request):
	
	product_data = requests.get('https://purse.io/api/v2/items/us?keywords=graphicscard&page=1')
	product_data = product_data.json()
	print(product_data)
	product_data = product_data['items'][:8]
	return render(request, 'users/home.html', {'items':product_data})

def termandcondition(request):
	return render(request, 'users/termandcondition.html')

def privacypolicy(request):
	return render(request, 'users/privacypolicy.html')

def contactus(request):
	if request.method == 'POST':
		name = request.POST['name']
		email = request.POST['email']
		subject = request.POST['subject']
		message = request.POST['message']

		to_email = settings.EMAIL_HOST_USER
		plaintext = "From: {}, Email:{}\n".format(name, email) + message
		
		from_email, to = None, to_email
		text_content = plaintext
		msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
		msg.send()

		messages.success(request, mark_safe(
					"Message sent, We will be back to you shortly."))
		return render(request, 'users/message_sent.html')

	return render(request, 'users/contact-us.html')

def aboutus(request):
	return render(request, 'users/about-us.html')

def signinregister(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'POST':
		if request.POST.get('register') != None:
			print(request.POST)
			form = UserRegisterForm(request.POST)
			if form.is_valid():
				user = form.save(commit=False)
				user.is_active = False
				user.save()
				print(request.POST['email'])
				form = ProfileRegisterForm(request.POST, instance=user.profile)
				form.save()
				current_site = get_current_site(request)
				mail_subject = 'Please, activate your Cartward account.'
				
				to_email = user.email
				plaintext = "Hello"
				htmly     = get_template('users/acc_active_email.html')

				d = {
					'user': user,
					'domain': current_site.domain,
					'uid': urlsafe_base64_encode(force_bytes(user.pk)),
					'token': default_token_generator.make_token(user),
				}

				from_email, to = None, to_email
				text_content = plaintext
				html_content = htmly.render(d)
				msg = EmailMultiAlternatives(mail_subject, text_content, from_email, [to])
				msg.attach_alternative(html_content, "text/html")
				msg.send()
				messages.info(request, mark_safe(
					'''Please confirm your email address to complete the registration. <a href="resend/{}/" class="alert-link">Resend 
					activation link</a> '''.format(user.pk)))
				return redirect('signin-register')
			else:
				messages.error(request, 'Invalid Registration Field')
				form1 = UserLoginForm()
		else:
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username=username, password=password)

			if user is not None:
				if user.is_active:
					login(request, user)
					usercart = jsondec.decode(user.cart.items)
					if request.session.get('cart') != None:
						usercart.extend(request.session['cart'])
						user.cart.items = json.dumps(usercart)
						user.cart.numberitem += request.session['numbercart']
					user.save()
					request.session.pop('cart', None)
					request.session.pop('numbercart', None)

					try:
						if request.GET['next']:
							return redirect(request.GET['next'])
					except Exception as e:
						return redirect('home-page')
				else:
					messages.error(request, 'Error')
					return redirect('signin-register')
			elif User.objects.filter(username=username).first():
				if User.objects.filter(username=username).first().profile.registration_status != "Complete":
					userpk = User.objects.filter(username=username).first().pk
					messages.error(request, mark_safe(
						'''Account not activated, Please complete registration. <a href="resend/{}/" class="alert-link">Resend activation 
						link</a> '''.format(userpk)))
					return redirect('signin-register')
				else:
					messages.error(request, 'Invalid Password or Username, Please try again')
					return redirect('signin-register')

			else:
				messages.error(request, 'Invalid Password or Username, Please try again')
				return redirect('signin-register')
	else:
		form = UserRegisterForm()
		form1 = UserLoginForm()
	return render(request, 'users/signinregister.html', {'form': form, 'form1': form1})

def activate(request, uidb64, token):
	try:
		uid = force_text(urlsafe_base64_decode(uidb64))
		user = User.objects.get(pk=uid)
	except(TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None
	if user is not None and default_token_generator.check_token(user, token):
		user.is_active = True
		user.profile.registration_status = "Complete"
		url = 'https://www.blockonomics.co/api/new_address'
		headers = {'Authorization': "Bearer " + 'NpoOY9tGZVFGDtda0VnqdWbfKrtGO0kx4o6XB0oXal0'}
		r = requests.post(url, headers=headers)
		print(r.json())
		if r.status_code == 200:
			user.profile.btcaddress = r.json()['address']

		user.save()
		messages.success(request, 'Confirmed. Now you can login and start shopping.')

		return redirect('signin-register')
	else:
		return messages.error(request, 'Link invalid')

def resend(request, pk):
	current_site = get_current_site(request)
	mail_subject = 'Please, Activate your Cartward account.'
	user = User.objects.filter(pk=pk).first()
	to_email = user.email
	plaintext = "Hello"
	htmly     = get_template('users/acc_active_email.html')

	d = {
		'user': user,
		'domain': current_site.domain,
		'uid': urlsafe_base64_encode(force_bytes(user.pk)),
		'token': default_token_generator.make_token(user),
	}

	from_email, to = None, to_email
	text_content = plaintext
	html_content = htmly.render(d)
	msg = EmailMultiAlternatives(mail_subject, text_content, from_email, [to])
	msg.attach_alternative(html_content, "text/html")
	msg.send()

	messages.info(request, mark_safe(
		'''Email sent! Please confirm your email address  to complete the registration . <a href="resend/{}/" class="alert-link">Resend 
		activation link</a> '''.format(user.pk)))
	return redirect('signin-register')

@login_required
def logout_view(request, *args, **kwargs):
    logout(request)
    return HttpResponseRedirect(reverse('home-page'))

@login_required
def profile(request):
	if request.method == 'POST':
		u_form = UserUpdateForm(request.POST, instance=request.user)
		p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
		if u_form.is_valid() and p_form.is_valid():
			u_form.save()
			p_form.save()
			messages.success(request, 'Successfully changed account informations')
			return redirect('profile-page')
	else:
		form = UserUpdateForm(instance=request.user)
		form2 = ProfileUpdateForm(instance=request.user.profile)
		return render(request, 'users/profile.html',{'form': form, 'form2': form2})

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {'form': form})

# def addressbook(request):
# 	if request.method == 'GET':
# 		addresses = Address.objects.filter(owner=request.user)
# 		return render(request, 'users/addressbook.html')

@login_required
def orders(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'GET':
		orders = Order.objects.filter(owner=request.user)
		curated_data = []
		
		for order in orders:
			print(order.items)
			product = jsondec.decode(order.items.replace("'", "\"").replace('None', 'null').replace('False', 'false').replace('True','true').replace("\\","/"))
			curated_data.append({'order':order, 'product':product})
		
		paginator = Paginator(curated_data, 10)
		page_number = request.GET.get('page')
		page_obj = paginator.get_page(page_number)

		return render(request, 'users/orders.html', {'page_obj':page_obj})

@login_required
def orderdetails(request, pk):
	if request.method == 'GET':
		status = {'Order Placed': ''' 
			<span class="dot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
		  ''',
		  'Order Purchased': ''' 
			<span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
		   ''',
		   'Shipment Received':''' 
		   	<span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
		    ''',
			'Shipped': ''' 
			<span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill "><span class="negdot"></span>
			 ''',
			'Delivered': ''' 
			<span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			<hr class="flex-fill track-line"><span class="dot"></span>
			 '''}
			   
		order = Order.objects.filter(pk=pk).first()
		track_html = status[order.delivery_status] 
		address_html = '<p>{}<br>{}<br>{}<br>{}<br>{}<br>{}<br>{}<br>Ph: {}</p>'.format((order.address.first_name + ' ' + order.address.last_name), order.address.address_line_2, order.address.address_line_1, order.address.state, order.address.city, order.address.postalcode, order.address.country, order.address.phonenumber)
		

		return render(request, 'users/orderdetails.html', {'order':order,'track_html': track_html, 'address_html': address_html, 'carrier': order.shipping})


def deposit(request):
	if request.method == 'GET':
		
		invoice = Btcinvoice.objects.create(
				address=request.user.profile.btcaddress, owner=request.user)
		return HttpResponseRedirect(reverse('track_payment', kwargs={'pk':invoice.id}))

# def exchanged_rate(amount):
#     url = "https://www.blockonomics.co/api/price?currency=USD"
#     r = requests.get(url)
#     response = r.json()
#     return amount/response['price']

def track_invoice(request, pk):
    invoice_id = pk
    invoice = Btcinvoice.objects.get(id=invoice_id)
    data = {
            'address': invoice.address,
            'status':Btcinvoice.STATUS_CHOICES[invoice.status+1][1],
            'invoice_status': invoice.status,
        }

    return render(request,'users/deposit.html',data)

    
    
def receive_payment(request):
    
	if (request.method != 'GET'):
		return 
    
	txid  = request.GET.get('txid')
	value = request.GET.get('value')
	status = request.GET.get('status')
	addr = request.GET.get('addr')
	invoice = Btcinvoice.objects.get(address = addr)
    
	invoice.status = int(status)
	if (int(status) == 0):
		user = invoice.owner
		user.profile.balance += value
		user.save()
		mail_subject = 'Account deposit.'
		to_email = user.profile.email
		plaintext = "Hello"
		htmly     = get_template('users/account_deposit.html')

		d = {
			'user': user,
			'amount': value
		}

		from_email, to = None, to_email
		text_content = plaintext
		html_content = htmly.render(d)
		msg = EmailMultiAlternatives(mail_subject, text_content, from_email, [to])
		msg.attach_alternative(html_content, "text/html")
		msg.send()
	invoice.txid = txid
	invoice.save()
	return HttpResponse(200)

def handler404(request, exception):
    return render(request, 'users/404.html', status=404)


def handler500(request, *args, **argv):
    return render(request, 'users/500.html', status=500)