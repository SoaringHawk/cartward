from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.urls import reverse
import requests
import ast
import sys
sys.path.append('../users')
from users.models import Cart, Address, Order
import json
from bs4 import BeautifulSoup
from django.contrib.auth.decorators import login_required
import time
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from random import choice
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.contrib.sites.shortcuts import get_current_site
# Create your views here.

def search(request):
	if request.method == 'POST':
		search_query = request.POST['search']
		if 'https://' in search_query:
			search_query = search_query.replace('?', '/')
			search_query = search_query.split('dp/')
			search_query = search_query[1].split('/')
			search_query = search_query[0]
			return HttpResponseRedirect(reverse('product-page', kwargs={'slug': search_query})) 
			
		else:
			search_query = search_query.replace(" ", "_")
			return HttpResponseRedirect(reverse('list-page', kwargs={'query_slug': search_query, 'page_slug': '1',})) 
		
	return HttpResponse('')


def product(request, slug):
	product_data = requests.get('https://purse.io/api/v2/items/US/{}'.format(slug))
	product_data = product_data.json()
	asin = product_data['asin']
	selections = {}

	
	product = get_appseller(asin)
	product = product.json()

	weight = product['package_dimensions']['weight']['value']
	length = product['package_dimensions']['length']['value']
	height = product['package_dimensions']['height']['value']
	width = product['package_dimensions']['width']['value']
	product_data['weight'] = weight
	product_data['height'] = height
	product_data['length'] = length
	product_data['width'] = width 
	
	product_data['description'] = product_data['description'].replace("'","").replace("\"","").replace(":","").replace(",","")
	product_data['name'] = product_data['name'].replace("'","").replace("\""," Inches").replace(":","").replace(",","")
	for elt in product_data['variations']:
		elt['name'] = elt['name'].replace("'","").replace("\"","").replace(":","").replace(",","")
	print(product_data)

	html = ''
	for variation in product_data['variations']:
		if selections.get(variation['vector']) == None:
			selections[variation['vector']] = [variation]
		else:
			selections[variation['vector']].append(variation)

	for selection in selections.keys():
		option = ''
		for opt in selections[selection]:
			if opt['asin'] == asin:
				text = "selected = 'selected' "
			else:
				text = " style='' "

			if opt['limited'] == True:
				text2 = "(Selection not available)"
			else:
				text2 = ""

			option += ''' 
				<option {} value="{}"  >{} {}</option>\n
			 '''.format(text, opt['asin'], opt['name'], text2)

		html += ''' 
			<div class="form-row">
				<div class="form-group col">
					<label class="font-weight-bold text-dark text-2">{}</label>
					<select class="form-control" id="selection" onchange="check_asin(this)">
						{}
					</select>
				</div>
			</div>\n
		 '''.format(selection, option)

	

	return render(request, 'orders/product.html', {'product': product_data, 'raw': html})

def listing(request, query_slug, page_slug):
	query_slug = query_slug.replace("_", " ")
	product_data = requests.get('https://purse.io/api/v2/items/us?keywords={}&page=1'.format(query_slug))
	product_data = product_data.json()
	print(product_data)
	product_data = product_data['items']

	return render(request, 'orders/search.html', {'search_query': query_slug, 'product': product_data, 'delete_footer': 'true'})

def proxy_generator():
	response = requests.get("https://sslproxies.org/")
	soup = BeautifulSoup(response.content, 'html5lib')
	proxy = {'https': choice(list(map(lambda x:x[0]+':'+x[1], list(zip(map(lambda x:x.text, soup.findAll('td')[::8]), map(lambda x:x.text, soup.findAll('td')[1::8])))))),
			'http': choice(list(map(lambda x:x[0]+':'+x[1], list(zip(map(lambda x:x.text, soup.findAll('td')[::8]), map(lambda x:x.text, soup.findAll('td')[1::8]))))))}
    
	return proxy

def get_appseller(asin):
    
	while True:
		try:
			proxy = proxy_generator()
			proxy['https'] = "http://"+ proxy['https']
			proxy['http'] = "http://"+ proxy['http']
			response = requests.request("get", "https://api.sellerapp.com/free_tool/product/details?product_id={}".format(asin), proxies=proxy, timeout=7, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36"})
			break
			# if the request is successful, no exception is raised
		except:
			print("Connection error, looking for another proxy")
			pass
	return response 

def add_to_cart(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'POST':
		if request.POST.get('wishlist'):
			search_query = request.POST['wishlist']
		
			url = 'https://purse.io/api/v2/wishlist'
			data = {'discount': 0.1,
					'items': [],
					'url':search_query}
			r = requests.post(url,data=data)
			wishlist= r.json()
			print(wishlist)
			wishlist_to_add = []
			for item in wishlist['items']:
				product_data = requests.get('https://purse.io/api/v2/items/US/{}'.format(item['asin']))
				product_data = product_data.json()
				asin = product_data['asin']
				selections = {}
	
				product = get_appseller(asin)
				product = product.json()
				weight = product['package_dimensions']['weight']['value']
				length = product['package_dimensions']['length']['value']
				height = product['package_dimensions']['height']['value']
				width = product['package_dimensions']['width']['value']
				product_data['weight'] = weight
				product_data['height'] = height
				product_data['length'] = length
				product_data['width'] = width
				product_data['qty'] = item['quantity']
				product_data['description'] = product_data['description'].replace("'","").replace("\"","").replace(":","").replace(",","")
				product_data['name'] = product_data['name'].replace("'","").replace("\"","").replace(":","").replace(",","")
				product_data = json.dumps(product_data)
				product_data = product_data.replace("'", "\"").replace('None', 'null').replace('False', 'false').replace('True','true').replace("\\","/")
				print(product_data)
				product_data = json.loads(product_data)
				wishlist_to_add.append(product_data)

				time.sleep(5)

			user = request.user 
			if user.is_authenticated:
				usercart = jsondec.decode(user.cart.items)
				usercart.extend(wishlist_to_add)
				user.cart.items = json.dumps(usercart)
				user.cart.numberitem += 1
				user.save()
			else:
				if request.session.get('cart') != None:
					request.session['cart'].extend(wishlist_to_add)
					request.session['numbercart'] += 1
				else:
					request.session['cart'] = wishlist_to_add
					request.session['numbercart'] = 1
			return HttpResponseRedirect(reverse('cart-page'))
		

		else:

			specification = request.POST['specification']
			specification = specification.replace("'", "\"").replace('None', 'null').replace('False', 'false').replace('True','true').replace("\\","/")
			print(specification)
			specification = json.loads(specification)
			specification['qty'] = 1

			user = request.user 
			if user.is_authenticated:
				usercart = jsondec.decode(user.cart.items)
				usercart.append(specification)
				user.cart.items = json.dumps(usercart)
				user.cart.numberitem += 1
				user.save()
			else:
				if request.session.get('cart') != None:
					request.session['cart'].append(specification)
					request.session['numbercart'] += 1
				else:
					request.session['cart'] = [specification]
					request.session['numbercart'] = 1
		return JsonResponse({})

def get_cart(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'GET':
		cart = None
		if request.user.is_authenticated:
			user = request.user
			usercart = jsondec.decode(user.cart.items)
			cart = usercart
			totalprice = 0
			totalweight = 0
			for item in usercart:
				totalprice += float(item['qty'])*float(item['fiat_price'])
				totalweight += float(item['weight'])*float(item['qty'])
		else:
			cart = request.session.get('cart')
			totalprice = 0
			totalweight = 0
			if cart != None:
				for item in cart:
					totalprice += float(item['qty'])*float(item['fiat_price'])
					totalweight += float(item['weight'])*float(item['qty'])

		return render(request, 'orders/cart.html', {'cart' : cart, 'cart_subtotal': "%.2f" %totalprice, 'total_weight': totalweight})

def update_cart(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'POST':
		query = dict(request.POST)
		query.pop('csrfmiddlewaretoken')
		user = request.user 
		if user.is_authenticated:
			
			modified = {}
			usercart = jsondec.decode(user.cart.items)
			print(user.cart.items)
			for req in query.keys():
				totalprice = 0
				totalweight = 0
				for item in usercart:
					print(user.cart.items)
					if item['asin'] == req:
						item['qty'] = int(request.POST[req])
						modified[item['asin']] = item['qty']
					totalprice += float(item['qty'])*float(item['fiat_price'])
					totalweight += float(item['weight'])*float(item['qty'])
			print(user.cart.items)
			user.cart.items = json.dumps(usercart)
			user.save()
						
		else:
			modified = {}
			if request.session.get('cart') != None:
				request.session['cart'].append(specification)
				for req in query.keys():
					totalprice = 0
					totalweight = 0
					for item in request.session['cart']:
						if item['asin'] == req:
							item['qty'] = int(request.POST[req])
							modified[item['asin']] = item['qty']
						totalprice += float(item['qty'])*float(item['fiat_price'])
						totalweight += float(item['weight'])*float(item['qty'])

			else:
				request.session['cart'] = [specification]
				request.session['numbercart'] = 1

				
		print(user.cart.items)
	
	return JsonResponse({ 'cart_subtotal':"%.2f" %totalprice ,'total_weight':totalweight,'modified':modified})

def get_shipping(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'POST':
		data = [('act','ShippingCalculator../shipping-calculator-results'),
				('cmscountry', 'us'),
				('cmslanguage', 'en'),
				('postingpageurl',' /en/shipping-calculator'),
				('shippingcalculator.warehouseid', 7),
				("shippingcalculator.country", request.POST['country']),
				("shippingcalculator.city", ""),
				("shippingcalculator.postalcode", ""),
				]
		
		if request.user.is_authenticated:
			usercart = jsondec.decode(request.user.cart.items)
			
			print(usercart)
			numbox = 0
			for item in usercart:
				for qty in range(int(item['qty'])):
					data.append(("shippingcalculator.scaleweight_units", "lb")),
					data.append(('shippingcalculator.scaleweight_val', int(round(float(item['weight']),0)) + 1))
					data.append(('box.scaleweightslider', int(round(float(item['weight']),0)) + 1))
					data.append(('shippingcalculator.boxvalue_amt', float(item['fiat_price'])))
					data.append(('shippingcalculator.boxvalue_code',  'USD'))
					data.append(('shippingcalculator.dimlength',  int(round(float(item['length']),0)) + 1))
					data.append(('box.dimslider',  int(round(float(item['length']),0)) + 1))
					data.append(('shippingcalculator.dimwidth', int(round(float(item['width']),0)) + 1))
					data.append(('box.dimslider', int(round(float(item['width']),0)) + 1))
					data.append(('shippingcalculator.dimheight', int(round(float(item['height']),0)) + 1))
					data.append(('box.dimslider', int(round(float(item['height']),0)) + 1))

					numbox += 1
			data.append(('shippingcalculator.numboxes',numbox))
		else:
			if request.session.get('cart') != None:
				numbox = 0
				for item in request.session['cart']:
					for qty in range(int(item['qty'])):
						data.append(("shippingcalculator.scaleweight_units", "lb")),
						data.append(('shippingcalculator.scaleweight_val', int(round(float(item['weight']),0)) + 1))
						data.append(('box.scaleweightslider', int(round(float(item['weight']),0)) + 1))
						data.append(('shippingcalculator.boxvalue_amt', float(item['fiat_price'])))
						data.append(('shippingcalculator.boxvalue_code',  'USD'))
						data.append(('shippingcalculator.dimlength',  int(round(float(item['length']),0)) + 1))
						data.append(('box.dimslider',  int(round(float(item['length']),0)) + 1))
						data.append(('shippingcalculator.dimwidth', int(round(float(item['width']),0)) + 1))
						data.append(('box.dimslider', int(round(float(item['width']),0)) + 1))
						data.append(('shippingcalculator.dimheight', int(round(float(item['height']),0)) + 1))
						data.append(('box.dimslider', int(round(float(item['height']),0)) + 1))

						numbox += 1
				data.append(('shippingcalculator.numboxes',numbox))

	
		print(data)
		url = 'https://www.shipito.com/en/shipping-calculator-results'
		
		r = requests.post(url,data= data)
		shippingprice = r.text
		soup = BeautifulSoup(shippingprice, 'html.parser')
		prices = soup.find_all('tr')
		data = []
		
		print(prices)
		for tr in prices:
			try:
				if tr.td['class'][0] == 'carrier-logo':
					ship_data = {}
					print(tr.td.text)
					if 'Shipito Priority Parcel' not in tr.td.text:
						ship_data['service'] = (tr.td.text).replace("\n","").replace("\r","")
						ship_data['usdamount'] = float(str(tr.span.text).replace('$','').replace('USD','').replace(' ','')) + (numbox*5)
						data.append(ship_data)
					print(tr.span.text)
			except:
				pass
		print(data)
		return JsonResponse(data, safe=False)

def delete_item(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'POST':
		item_to_delete = request.POST['item']
		user = request.user 
		if user.is_authenticated:
			usercart = jsondec.decode(user.cart.items)
			cart_copy = usercart[:]
			
			for item in usercart:
				if item['asin'] == item_to_delete:
					cart_copy.remove(item)
			user.cart.items = json.dumps(cart_copy)
			user.save()
						
		else:
			modified = {}
			if request.session.get('cart') != None:
				# request.session['cart'].append(specification)
				# request.session['numbercart'] -= 1

				cart_copy = request.session['cart'][:]
				for item in request.session['cart']:
					
					if item['asin'] == item_to_delete:
						cart_copy.remove(item)
				request.session['cart'] = cart_copy
			
						
		# print(request.user.cart.items)
		
		return JsonResponse({'item': item_to_delete})

def get_item_number(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == "GET":
		totalitem = 0
		user = request.user 
		if user.is_authenticated:
			totalitem = 0
			usercart = jsondec.decode(user.cart.items)
			for item in usercart:
				totalitem += 1
						
		else:
			if request.session.get('cart') != None:
				totalitem = 0
				for item in request.session['cart']:
					totalitem += 1
		return JsonResponse({'item_number': totalitem})

@login_required
def checkout(request):
	jsondec = json.decoder.JSONDecoder()
	if request.method == 'GET':
		print(request.POST)
		# try:
		country = request.session['country']
		state = request.session['state']
		postalcode = request.session['postalcode']
		carrier = request.session['carrier']
		
		subtotal = request.session['subtotal']
		shipping = request.session['shippingcost']
		total = request.session['totalamount']
		# except:
		# 	country = ''
		# 	state = ''
		# 	postalcode =''
		# 	carrier = ''
		# 	subtotal = ''
		# 	shipping = ''
		# 	total = ''
		data = [('act','ShippingCalculator../shipping-calculator-results'),
				('cmscountry', 'us'),
				('cmslanguage', 'en'),
				('postingpageurl',' /en/shipping-calculator'),
				('shippingcalculator.warehouseid', 7),
				("shippingcalculator.country", country),
				("shippingcalculator.city", ""),
				("shippingcalculator.postalcode", ""),
				]
		usercart = jsondec.decode(request.user.cart.items)
		subtotal = 0
		numbox = 0
		for item in usercart:
			subtotal += float(item['qty'])*float(item['fiat_price'])
			for qty in range(int(item['qty'])):
				data.append(("shippingcalculator.scaleweight_units", "lb")),
				data.append(('shippingcalculator.scaleweight_val', int(round(float(item['weight']),0)) + 1))
				data.append(('box.scaleweightslider', int(round(float(item['weight']),0)) + 1))
				data.append(('shippingcalculator.boxvalue_amt', float(item['fiat_price'])))
				data.append(('shippingcalculator.boxvalue_code',  'USD'))
				data.append(('shippingcalculator.dimlength',  int(round(float(item['length']),0)) + 1))
				data.append(('box.dimslider',  int(round(float(item['length']),0)) + 1))
				data.append(('shippingcalculator.dimwidth', int(round(float(item['width']),0)) + 1))
				data.append(('box.dimslider', int(round(float(item['width']),0)) + 1))
				data.append(('shippingcalculator.dimheight', int(round(float(item['height']),0)) + 1))
				data.append(('box.dimslider', int(round(float(item['height']),0)) + 1))
				
				numbox += 1
		data.append(('shippingcalculator.numboxes',numbox))
		
		url = 'https://www.shipito.com/en/shipping-calculator-results'
		
		r = requests.post(url,data= data)
		shippingprice = r.text
		soup = BeautifulSoup(shippingprice, 'html.parser')
		prices = soup.find_all('tr')
		data = []
		
		# print(prices)
		for tr in prices:
			try:
				if tr.td['class'][0] == 'carrier-logo':
					ship_data = {}
					# print(tr.td.text)
					if 'Shipito Priority Parcel' not in tr.td.text:
						ship_data['service'] = (tr.td.text).replace("\n","").replace("\r","")
						ship_data['usdamount'] = float(str(tr.span.text).replace('$','').replace('USD','').replace(' ','')) + (numbox*5)
						data.append(ship_data)
					# print(tr.span.text)
			except:
				pass
		shipping = 0
		for elt in data:
			print(elt)
			print(carrier)
			if carrier ==  elt['service']:
				shipping = elt['usdamount']
		
	
		total = float(subtotal) + float(shipping)
		total ="%.2f" % total

		cart = request.user.cart
		cart.carttotal = subtotal
		cart.shippingtotal = shipping
		print(total)
		cart.total = float(total)

		cart.save()
		subtotal = "%.2f" % subtotal
		

		return render(request, 'orders/checkout.html', {'cart':usercart, 'subtotal':subtotal, 'shipping':shipping, 'service':carrier, 'total':float(total), 'countryselected': country, 'stateselected': state, 'postalselected': postalcode})
	
		

@login_required
def place_order(request):
	jsondec = json.decoder.JSONDecoder()
	print('there')
	if request.method == 'POST':
		print(request.POST)
		user = request.user
		print('---------------------')
		print(user.cart.carttotal)
		usercart = jsondec.decode(user.cart.items)
		for item in usercart:
			item.pop('variations', None)

		address = Address(owner=request.user, first_name=request.POST['firstname'], last_name=request.POST['lastname'], address_line_1=request.POST['addressline1'], 
		address_line_2=request.POST['addressline2'], city=request.POST['city'], state=request.POST['state'], postalcode=request.POST['zipcode'],
		country=request.POST['country'], phonenumber= request.POST['phonenumber'] )
		address.save()
		order = Order(owner= request.user, address= address, items=usercart, shipping=request.POST['service'], carttotal= user.cart.carttotal, shippingtotal=user.cart.shippingtotal, total= float(user.cart.total) )
		order.save()

		user.cart.items = '[]'
		user.save()

		items = "*"
		items += usercart[0]['name']

		if len(usercart) > 1:
			items += "and more..."
		else:
			items += "*"
		
		# mail_subject = 'Order confirmation.'
		# message = render_to_string('orders/order_email.html', {
		# 	'user': user,
		# 	'items': items,
		# 	'address1': request.POST['addressline1'],
		# 	'address2': request.POST['addressline2']
		# })
		to_email = request.user.profile.email
		# # email = EmailMessage(
		# # 	mail_subject, message, to=[to_email]
		# # )
		# # email.send()

		# send_mail(
		# mail_subject,
		# 'Hello',
		# None,
		# [to_email],
		# html_message=message,
		# )
		current_site = get_current_site(request)
		plaintext = "Hello"
		htmly     = get_template('orders/order_email.html')

		d = { 'user': user, 'items': items, 'address1': request.POST['addressline1'], 'address2': request.POST['addressline2'], 'domain': current_site.domain, 'pk': order.pk}

		subject, from_email, to = 'Order Confirmation', None, to_email
		text_content = plaintext
		html_content = htmly.render(d)
		msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
		msg.attach_alternative(html_content, "text/html")
		msg.send()

		return render(request,'orders/checkout_success.html', {'pk':order.pk})
	
def wishlist(request):
	if request.method == "GET":
		return render(request, 'orders/wishlist.html')


def query_page(request):
	if request.method == "POST":
		page = request.POST['page']
		print(request.POST)
		query_slug = request.POST['query'].replace("_", " ")

		product_data = requests.get('https://purse.io/api/v2/items/us?keywords={}&page={}'.format(query_slug, page))
		product_data = product_data.json()
		print(product_data)
		product_data = product_data['items']
		product_html = ''
		for item in product_data:
			
			product_html += ''' <div class="col-12 col-sm-6 col-lg-3 product" >
										<!-- <a href="shop-product-sidebar-left.html">
											<span class="onsale">Sale!</span>
										</a> -->
										<span class="product-thumb-info border-0">
											<!-- <a href="shop-cart.html" class="add-to-cart-product bg-color-primary">
												<span class="text-uppercase text-1">Add to Cart</span>
											</a> -->
											<a href="/US/product/{}/">
												<span class="product-thumb-info-image">
													<img alt="" class="img-fluid" src="{}" style="max-height: 250px;" >
												</span>
											</a>
											<span class="product-thumb-info-content product-thumb-info-content pl-0 bg-color-light">
												<a href="/US/product/{}/">
													<h4 class="text-4 text-primary">{}</h4>
													<span class="price">
														<ins><span class="amount text-dark font-weight-semibold">${}</span></ins>
													</span>
												</a>
											</span>
										</span>
									</div>\n  '''.format(item['asin'],item['images']['medium'],item['asin'],item['name'],item['fiat_price'])
	print(product_html)

	return JsonResponse(product_html, safe=False)

def prohibited(request):
	if request.method == 'GET':
		return render(request, 'orders/prohibited.html')

def faq(request):
	if request.method == 'GET':
		return render(request, 'orders/faq.html')

def get_prohibited_item(request):
	if request.method == "POST":
		curated_data = []
		html = ''
		country = request.POST['country']
		url = " https://www.shipito.com/en/help/tutorials/prohibited-items/country-specific?filter.country={}".format(country)
		r = requests.get(url)
		data = r.text
		soup = BeautifulSoup(data,'html.parser')
		curr = soup.find_all('div', attrs={'class':'nested-panel'})
		for div in curr:
			ps = div.find_all('p')
			examples = []
			lis = div.find_all('li')
			lihtml = ''
			for li in lis:
				lihtml += '<li>{}</li>'.format(li.text.replace('\r','').replace('\n','').replace('\t','').strip())

			html += ''' 
						<div class="col-lg-4">

					<h4>{}</h4>
					<span>{}</span>
					<ul>
						{}
						
					</ul>

				</div>
			 '''.format(ps[0].text, ps[1].text, lihtml)
			

		# print(curr)
		return JsonResponse({'html': html}, safe=False)

def save_shipping(request):
	if request.method == 'POST':
		
		request.session['country'] = request.POST['country']
		request.session['state'] = request.POST['state']
		request.session['postalcode'] = request.POST['postalcode']
		request.session['carrier'] = request.POST['carrier']
		request.session['subtotal'] = request.POST['subtotal']
		request.session['shippingcost'] = request.POST['shippingcost']
		request.session['totalamount'] = request.POST['totalamount']

		return JsonResponse({})