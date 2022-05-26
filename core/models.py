from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
from django.core import validators
from django_countries.fields import CountryField

# Create your models here.

CATEGORY_CHOICES = (
    ('S', 'Shirts'),
    ('SW', 'Sport wears'),
    ('OW', 'Outwears'),
    ('K', 'Kids'),
)


LABEL_CHOICES = (
    ('P', 'primary-color'),
    ('S', 'secondry-color'),
    ('D', 'danger-color')
)




class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.FloatField()
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=2)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    description = models.TextField(null=True)
    info = models.TextField(null=True)
    slug = models.SlugField(blank=True, unique=True)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('core:product', kwargs={'slug' : self.slug})
    
    def save(self, *args, **kwargs): 
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)


class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f'{self.quantity}x({self.item.title})  for  {self.user}'

    def total_item_price(self):
        return self.item.price * self.quantity

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    billing_address = models.ForeignKey('BillingAddress', on_delete=models.SET_NULL, blank=True, null=True)
    payment_info = models.ForeignKey('Payment', on_delete=models.SET_NULL, blank=True, null=True)
    def __str__(self):
        if self.ordered == True:
            return 'Completed Order for '  + self.user.username 
        return 'in Progress Order for '  + self.user.username
    
    def total_price(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.total_item_price()
        return total
    
    def count_all_items(self):
        items_num = 0
        for i in self.items.all():
            quantity = i.quantity
            items_num += quantity
        return items_num
    
    
class BillingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=256)
    apartment_address = models.CharField(max_length=256)
    country = CountryField(multiple=False)
    zip_code = models.IntegerField()
    
    def __str__(self):
        return f'billing address for {self.user.username}'
    
    


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=64)
    dollars = models.FloatField()
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username} payment information'