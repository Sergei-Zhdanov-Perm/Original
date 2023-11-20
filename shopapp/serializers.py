from rest_framework import serializers

from .models import Product, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = (
            "pk",
            "name",
            "description",
            "price",
            "discount",
            "created_at",
            "archived",
            "preview",
        )


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ("pk",
                  "delivery_address",
                  "user",
                  "products",
                  "promocode",
                  "created_at",
                  )


