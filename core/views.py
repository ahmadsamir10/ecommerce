from django.conf import settings
from django.http import  Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views.generic import  ListView, DetailView, View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from .models import Order, Item, OrderItem, BillingAddress, Payment, CATEGORY_CHOICES
from django.utils import timezone
from .forms import CheckoutForm
import stripe
import json
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY


class IndexView(ListView):
    template_name = 'ecommerce/home-page.html'
    model = Item
    context_object_name = 'items'
    paginate_by = 4
    extra_context = {'cat_choices':CATEGORY_CHOICES}



class ItemsByCategory(DetailView):

    def get(slef, request, cat_name, *args, **kwargs):
        items_list = Item.objects.filter(category=cat_name)
        if items_list:
            paginator = Paginator(items_list, 1)
            page_number = request.GET.get('page')
            items = paginator.get_page(page_number)

            context = {'items':items, 'cat_choices':CATEGORY_CHOICES}
            return render(request, 'ecommerce/itembycat.html', context)

        else:
            raise Http404()



class Product(DetailView):
    template_name = 'ecommerce/product-page.html'
    model = Item
    slug_url_kwarg = 'slug'
    context_object_name = 'item'
    
    
    

class PurchasedOrders(View):
    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user, ordered=True)
        print(orders)
        context = {'orders':orders}
        return render(request, 'ecommerce/purchased_orders.html', context)


    
        
class AddToCart(LoginRequiredMixin, View):
    def get(self, request, slug):
        item = get_object_or_404(Item, slug=slug)
        order_item, created = OrderItem.objects.get_or_create(item=item,
                                                 user=request.user,
                                                 ordered=False)
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity +=1
                order_item.save()
                messages.info(request, 'quantity updated')
            else:
                messages.info(request, 'added to your cart')
                order.items.add(order_item)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                user=request.user,
                ordered_date=ordered_date,
            )
            order.items.add(order_item)
            messages.info(request, 'added to your cart')
        return redirect('core:order-summary')





class RemoveFromCart(LoginRequiredMixin, View):
    def get(self, request, slug):
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(item=item,
                                           user=request.user,
                                           ordered=False)[0]
                
                if int(order_item.quantity) == 1:
                    order_item.delete()
                    messages.info(request, 'removed from your cart')

                else:
                    order_item.quantity -=1
                    order_item.save()
                    messages.info(request, '1 item removed from your cart')
                
                return redirect('core:order-summary')
            else:
                messages.warning(request, 'this item was not in your cart')
                return redirect('core:order-summary')
        
        else:
            messages.warning(request, 'you don\'t have an active order')
            return redirect('core:order-summary')


class RemoveAllItems(View):
    def get(self, request, slug):
        item = get_object_or_404(Item, slug=slug)
        order_qs = Order.objects.filter(user=request.user, ordered=False)
        if order_qs.exists():
            order = order_qs[0]
            
            if order.items.filter(item__slug=item.slug).exists():
                order_item = OrderItem.objects.filter(item=item,
                                           user=request.user,
                                           ordered=False)[0]
                order_item.delete()
                messages.info(request, 'removed from your cart')
                return redirect('core:order-summary')
            
            else:
                messages.warning(request, 'this item was not in your cart')
                return redirect('core:order-summary')
            
        else:
            messages.warning(request, 'you don\'t have an active order')
            return redirect('core:order-summary')
     
     
     
            
class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            context = {'order':order}
            return render(self.request, 'ecommerce/order_summary.html', context)
        except ObjectDoesNotExist:
            empty=True
            context = {'empty':empty}
            return render(self.request, 'ecommerce/order_summary.html', context)






class Checkout(View):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            if list(order.items.all()) == []:
                messages.warning(request, 'you don\'t have items to checkout')
                return redirect('core:order-summary')
            else:
                context = {'form' : CheckoutForm, 'order':order}
                return render(request, 'ecommerce/checkout-page.html', context)
        
        except ObjectDoesNotExist:
            raise Http404()
    
    def post(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            form = CheckoutForm(request.POST or None)
            if form.is_valid():
                
                street_address = form.cleaned_data['street_address']
                apartment_address = form.cleaned_data['apartment_address']
                country = form.cleaned_data['country']
                zip_code = form.cleaned_data['zip_code']
                #same_billing_address = form.cleaned_data['same_billing_address']
                #save_info = form.cleaned_data['save_info']
                payment_method = form.cleaned_data['payment_method']
                billing_address = BillingAddress(
                    user = request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip_code = zip_code,
                )

                billing_address.save()
                order.billing_address = billing_address
                order.save()
                
                if payment_method == 'S':   
                    return redirect('core:payment', 'stripe')
                
                elif payment_method == 'P':
                    return redirect('core:payment', 'paypal')
                else:
                    raise Http404()
            
            messages.warning(request, 'not valid informations')
            return redirect('core:checkout')
        
        except ObjectDoesNotExist:  
            messages.warning(request, 'you don\'t have an active order')
            return redirect('core:order-summary')
        


class PaymentView(View):
    def get(self, request, payment_method):
        order = Order.objects.get(user=request.user, ordered=False)
        context = {'order':order}
        if payment_method == 'stripe':
            return render(request, 'ecommerce/payment_stripe.html',context)
        
        elif payment_method == 'paypal':
            return render(request, 'ecommerce/payment_paypal.html')
        
        else:
            raise Http404()
        
    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        
        token = request.POST.get('stripeToken')
        
        try:
        # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
            amount=int(order.total_price() *100),
            currency="usd",
            source=token
            )
        
        
            payment=Payment()
            payment.user = request.user
            payment.stripe_charge_id = charge['id']
            payment.dollars = order.total_price()
            payment.save()

            order.ordered = True
            order.payment_info = payment
            order.save()

            messages.success(self.request, "Your order was successful!")
            return redirect("/")
        
        except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(request, f"{err.get('message')}")
            return redirect("/")
        
        except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
            messages.warning(request, "Rate limit error")
            return redirect("/")
        
        except stripe.error.InvalidRequestError as e:
        # Invalid parameters were supplied to Stripe's API
            messages.warning(request, "Invalid parameters")
            return redirect("/") 
           
        except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
            messages.warning(request, "Not authenticated")
            return redirect("/")  
        
        except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
            messages.warning(request, "Network error")
            return redirect("/")
        
        except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
            messages.warning(
                    request, "Something went wrong. You were not charged. Please try again.")
            return redirect("/")
        
        except Exception as e:
        # Something else happened, completely unrelated to Stripe
            print(e)
            messages.warning(
                    request, "A serious error occurred. We have been notifed.")
            return redirect("/")
        
        
