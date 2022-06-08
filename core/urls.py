from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('category/<cat_name>', views.ItemsByCategory.as_view(), name='itemsbycat'),
    path('product/<slug:slug>', views.Product.as_view(), name='product'),
    path('purchased_orders', views.PurchasedOrders.as_view(), name='purchased_orders'),
    path('add_to_cart/<slug:slug>', views.AddToCart.as_view(), name='add_to_cart'),
    path('remove_from_cart/<slug:slug>', views.RemoveFromCart.as_view(), name='remove_from_cart'),
    path('remove_all_item/<slug:slug>', views.RemoveAllItems.as_view(), name='remove_all_item'),
    path('order-summary/', views.OrderSummaryView.as_view(), name='order-summary'),
    path('checkout/', views.Checkout.as_view(), name='checkout'),
    path('validate_promocode/', views.ValidatePromCodeView.as_view(), name='validate_promocode'),
    path('payment/', views.PaymentView.as_view(), name='payment')
]

