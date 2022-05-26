from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


PAY_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'Paypal'),
)

class CheckoutForm(forms.Form):
    street_address = forms.CharField(required=True, widget=forms.TextInput(
        attrs={
            'class':'form-control',
            'placeholder':'1234 Main St',
            
        }))     
    
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(
        attrs={
            'class':'form-control',
            'placeholder':'Apartment or suite',
            
        }))
    
    country = CountryField().formfield(widget=CountrySelectWidget(
        attrs={
            'class':'custom-select d-block w-100'
        }))
    
    zip_code = forms.CharField(required=True, widget=forms.TextInput(
        attrs={
            'class':'form-control'
        }))
    
    same_billing_address = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    
    save_info = forms.BooleanField(widget=forms.CheckboxInput(), required=False)
    
    payment_method = forms.ChoiceField(widget=forms.RadioSelect, choices=PAY_CHOICES)