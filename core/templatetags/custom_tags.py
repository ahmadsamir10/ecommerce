from urllib import request
from django import template
from core.models import Order

register = template.Library()


@register.filter
def count_cart_items(user):
    if user.is_authenticated:
        qs = Order.objects.filter(user=user, ordered=False)
        if qs.exists():
            return qs[0].items.count()
        
    return 0



@register.filter
def mk_cats_list(cats_tuple):
    cat_list = []
    for cat in cats_tuple:
        cat_list.append([cat[0], cat[1]])
    return cat_list