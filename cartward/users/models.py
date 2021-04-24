from django.db import models
from django.contrib.auth.models import User


# Create your models here.

class Profile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	email = models.EmailField()
	registration_status = models.TextField(null=True)
	balance = models.FloatField(default=0.00)
	# email_change = models.EmailField(null=True)

	def __str__(self):
		return '{} Profile'.format(self.user.username)

	def save(self, *args, **kwargs):
		super(Profile, self).save(*args, **kwargs)

class Address(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	first_name = models.TextField(default='')
	last_name = models.TextField(default='')
	address_line_1 = models.TextField(default='')
	address_line_2 = models.TextField(null=True)
	state = models.TextField(default='')
	city = models.TextField(default='')
	postalcode = models.TextField(default='')
	country = models.TextField(default='')
	phonenumber = models.TextField(default='')

	def __str__(self):
		return '{} Address'.format(self.owner.username)

	def save(self, *args, **kwargs):
		super(Address, self).save(*args, **kwargs)


class Cart(models.Model):
	owner = models.OneToOneField(User, on_delete=models.CASCADE)
	items = models.TextField(null=True, default='[]') 
	numberitem = models.IntegerField(default=0)
	carttotal = models.IntegerField(default=0)
	shippingtotal = models.IntegerField(default=0)
	total = models.IntegerField(default=0)

	def __str__(self):
		return '{} Cart'.format(self.owner.username)

	def save(self, *args, **kwargs):
		super(Cart, self).save(*args, **kwargs)


class Order(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	address = models.ForeignKey(Address, on_delete=models.CASCADE)
	items = models.TextField(default='')
	shipping = models.TextField(default='')
	carttotal = models.IntegerField(default=0)
	shippingtotal = models.IntegerField(default=0)
	total = models.IntegerField(default=0)
	delivery_status = models.CharField(max_length=30,default='Order Placed',choices=[('Order Placed', 'Order Placed'), ('Order Purchased', 'Order Purchased'), ('Shipment Received', 'Shipment Received'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered')])
	def __str__(self):
		return '{} Order'.format(self.owner.username)

	def save(self, *args, **kwargs):
		super(Order, self).save(*args, **kwargs)
