from django import forms
from django.contrib.auth.models import Group
from django.forms import ModelForm

from .models import Product, Order


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = "name", "price", "description", "discount", "preview"

    images = forms.ImageField(
        # widget=forms.ClearableFileInput(attrs={"multiple": True})
        # Максим Семенюк
        # Куратор
        # 21 сентября, 2023 21:32
        # Откатите версию джанго до 4.2.2, либо не используйте
        # widget=forms.ClearableFileInput(attrs={"multiple": True})
        # так как джанго не поддерживает из коробки загрузку нескольких файлов из одной формы.
    )


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "delivery_address", "promocode", "user", "products"
        widgets = {"products": forms.CheckboxSelectMultiple,
                   "delivery_address": forms.Textarea(attrs={"cols": 35, "rows": 5})
                   }


class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = ["name"]


class CSVImportForm(forms.Form):
    csv_file = forms.FileField()
