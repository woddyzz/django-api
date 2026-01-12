from .models import *
from rest_framework import serializers
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['slug', 'title']

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField()

    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category_id', 'category']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]

class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    menu_item = MenuItemSerializer(read_only=True)
    menu_item_id = serializers.IntegerField()
    class Meta:
        model = Cart
        fields = ['user','menu_item_id', 'menu_item', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price']

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['order', 'menu_item', 'quantity', 'unit_price', 'price']
        read_only_fields = ['order', 'menu_item', 'quantity', 'unit_price', 'price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True, read_only=True)
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'items']

class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']