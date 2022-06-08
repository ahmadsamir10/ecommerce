from audioop import reverse
from django.conf import settings
from django.http import  Http404, JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect, get_list_or_404
from django.views.generic import  ListView, DetailView, View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from .models import Order, Item, OrderItem, BillingAddress, Payment, CATEGORY_CHOICES, PromoCode
from django.utils import timezone
from .forms import CheckoutForm
import stripe
# Create your views here.

stripe.api_key = settings.STRIPE_SECRET_KEY


class IndexView(ListView):
    template_name = 'ecommerce/home-page.html'
    context_object_name = 'items'
    paginate_by = 12
    extra_context = {'cat_choices':CATEGORY_CHOICES}
    def get_queryset(self):
        query = self.request.GET.get('search')
        if query is not None:
            queryset = Item.objects.filter( Q(title__icontains=query) | Q(description__icontains=query))
            return queryset
        else:
            return Item.objects.all().order_by('?')


class ItemsByCategory(ListView):
    template_name = 'ecommerce/itembycat.html'
    slug_url_kwarg = 'cat_name'
    context_object_name = 'items'
    paginate_by = 12
    extra_context = {'cat_choices':CATEGORY_CHOICES}
    
    def get_queryset(self):
        cat_name = self.kwargs.get(self.slug_url_kwarg)
        query = self.request.GET.get('search')
        if query is not None:
            filtered_items = Item.objects.filter(Q(title__icontains=query) | Q(description__icontains=query), category=cat_name)
            return filtered_items
        items_list = get_list_or_404(Item, category=cat_name)
        return items_list





class Product(DetailView):
    template_name = 'ecommerce/product-page.html'
    model = Item
    slug_url_kwarg = 'slug'
    context_object_name = 'item'
    
    
    

class PurchasedOrders(View):
    def get(self, request, *args, **kwargs):
        orders = Order.objects.filter(user=request.user, ordered=True)
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
                message = {
                    "status":"Already in your cart, quantity = ",
                    "cart":order.items.count(),
                    "quantity":order_item.quantity,
                    "item_total":f"{order_item.total_item_price()}",
                    "total": f"{order.total_price()}",  
                }
            else:
                message = {
                    "status":"added to your cart",
                    "cart":order.items.count()+1
                }
                order.items.add(order_item)
        else:
            ordered_date = timezone.now()
            order = Order.objects.create(
                user=request.user,
                ordered_date=ordered_date,
            )
            order.items.add(order_item)
            message = {
                    "status":"added to your cart",
                    "cart":order.items.count()
                }
        return JsonResponse(message)






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
                    message = {
                    "status":"quantity updated",
                    "cart":order.items.count(),
                    "quantity":order_item.quantity,
                    "item_total":f"{order_item.total_item_price()}",
                    "total": f"{order.total_price()}",  
                } 
                    return JsonResponse(message)
                else:
                    order_item.quantity -=1
                    order_item.save()
                    message = {
                    "status":"quantity updated",
                    "cart":order.items.count(),
                    "quantity":order_item.quantity,
                    "item_total":f"{order_item.total_item_price()}",
                    "total": f"{order.total_price()}",  
                } 
                
                return JsonResponse(message)
            else:
                messages.warning(request, 'this item was not in your cart')
                return redirect('core:order-summary')
        
        else:
            messages.warning(request, 'you don\'t have an active order')
            return redirect('core:order-summary')


class RemoveAllItems(LoginRequiredMixin, View):
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
                message = {
                    "status":"item '" + order_item.item.title + "' removed from your cart",
                    "total": f'{order.total_price()}',
                    "cart":order.items.count()
                }
                return JsonResponse(message)
            
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






class Checkout(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            if list(order.items.all()) == []:
                messages.warning(request, 'you don\'t have items to checkout')
                return redirect('core:order-summary')
            else:
                addresses = BillingAddress.objects.filter(user=request.user, save_info=True)
                context = {'form' : CheckoutForm, 'order':order, 'addresses':addresses}
                return render(request, 'ecommerce/checkout-page.html', context)
        
        except ObjectDoesNotExist:
            raise Http404()
    
    def post(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user=request.user, ordered=False)
            recent_address = request.POST.get('recent-addresses')
            if recent_address and BillingAddress.objects.filter(id=recent_address, user=request.user).exists():
                user_address = BillingAddress.objects.get(id=recent_address, user=request.user)
                order.billing_address = user_address
                order.save()
                return redirect('core:payment')
                
            form = CheckoutForm(request.POST or None)
            if form.is_valid():
                
                street_address = form.cleaned_data['street_address']
                apartment_address = form.cleaned_data['apartment_address']
                country = form.cleaned_data['country']
                zip_code = form.cleaned_data['zip_code']
                save_info = form.cleaned_data['save_info']
                billing_address = BillingAddress(
                    user = request.user,
                    street_address = street_address,
                    apartment_address = apartment_address,
                    country = country,
                    zip_code = zip_code,
                )
                if save_info:
                    billing_address.save_info = True
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                
                return redirect('core:payment')
                        
            messages.warning(request, 'not valid informations')
            return redirect('core:checkout')
        
        except ObjectDoesNotExist:  
            messages.warning(request, 'you don\'t have an active order')
            return redirect('core:order-summary')


class ValidatePromCodeView(LoginRequiredMixin, View):
    def post(self, request):
        code = request.POST.get('promocode-input')
        if code:
            if PromoCode.objects.filter(code=code).exists():
                promcode_instance = PromoCode.objects.get(code=code)
                if promcode_instance.still_active():
                    order_qs = Order.objects.filter(user=request.user, ordered=False)
                    if order_qs.exists():
                        order = order_qs[0]
                        if order.promo_code:
                            message = {"status":"already linked with promo code"}
                            return JsonResponse(message)
                        
                        order.promo_code = promcode_instance
                        order.save()
                        message = {
                            "success":True,
                            "code":promcode_instance.code,
                            "percent":promcode_instance.discount_value,
                            "deducted":f"{order.discount_amount()}",
                            "total":f"{order.total_after_discount()}",
                            "status":"successfully linked to you order"
                        }
                        return JsonResponse(message)
                        
                    message = {"status":"no active order"}
                    return JsonResponse(message)
                
                message = {"status":"promocode expired"}
                return JsonResponse(message)
            
            message = {"status":"invalid promocode"}
            return JsonResponse(message)
                    
        message = {"status":"no promocode entered"}
        return JsonResponse(message)
                



class PaymentView(LoginRequiredMixin, View):
    def get(self, request):
        order = get_object_or_404(Order, user=request.user , ordered=False)
        if order.billing_address:
            order = Order.objects.get(user=request.user, ordered=False)
            context = {'order':order}
            return render(request, 'ecommerce/payment_stripe.html',context)
        messages.warning(request, 'checkout the order first')
        return redirect('core:checkout')


    def post(self, request, *args, **kwargs):
        order = Order.objects.get(user=request.user, ordered=False)
        
        token = request.POST.get('stripeToken')
        
        try:
        # Use Stripe's library to make requests...
            charge = stripe.Charge.create(
            amount=int(order.total_after_discount() *100),
            currency="usd",
            source=token
            )
        
        
            payment=Payment()
            payment.user = request.user
            payment.stripe_charge_id = charge['id']
            payment.dollars = order.total_after_discount()
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
        
        
