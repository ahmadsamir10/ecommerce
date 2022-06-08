from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.urls import reverse
import secrets
from datetime import datetime
from django_countries.fields import CountryField

# Create your models here.

CATEGORY_CHOICES = (
    ('electronics', 'Electronics'),
    ('fashion', 'Fashion'),
    ('home', 'Home'),
    ('perfumes', 'Perfumes'),
)


LABEL_CHOICES = (
    ('P', 'primary-color'),
    ('S', 'secondry-color'),
    ('D', 'danger-color')
)




class Item(models.Model):
    title = models.CharField(max_length=100)
    old_price = models.FloatField(null=True, blank=True)
    price = models.FloatField()
    main_image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=11)
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
    
class ItemImage(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='item_images/')
    
    def __str__(self):
        return f'image for {self.item.title}'


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
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL, null=True, blank=True)
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
    
    def discount_amount(self):
        if self.promo_code:
            total = self.total_price()
            code_discount = self.promo_code.discount_value
            discount_amount = total * (code_discount/100)
            return discount_amount
        return 0
    
    def total_after_discount(self):
        if self.promo_code:
            return self.total_price() - self.discount_amount()
        return self.total_price()
        
    
    
class BillingAddress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=256)
    apartment_address = models.CharField(max_length=256)
    country = CountryField(multiple=False)
    zip_code = models.IntegerField()
    save_info = models.BooleanField(default=False)
    
    def __str__(self):
        return f'billing address for {self.user.username}'
    
    def content(self):
        return f"{self.street_address}, {self.apartment_address}, {self.country.name}, zip:{self.zip_code}"
    
    


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_charge_id = models.CharField(max_length=64)
    dollars = models.FloatField()
    time_stamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user.username} payment information'
    


class PromoCode(models.Model):
    code_exp_date = models.DateField()
    code = models.CharField(max_length=30, null=True, blank=True)
    discount_value = models.IntegerField()
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.code
    
    def save(self, *args, **kwargs):
        if not self.code:
             self.code = secrets.token_urlsafe(16)
        super(PromoCode, self).save(*args, **kwargs)
    
    def still_active(self):
        exp_date = self.code_exp_date.strftime("%m/%d/%Y")
        now = datetime.now()
        today = now.strftime("%m/%d/%Y")
        if exp_date <= today:
            self.active = False
            self.save()
            return False
        else:
            return True 
