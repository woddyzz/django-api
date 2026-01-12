from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response 
from rest_framework.permissions import BasePermission, SAFE_METHODS, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from .models import *
from .serializers import *
from django.contrib.auth.models import User, Group
from rest_framework.filters import OrderingFilter

# Create your views here.
class isManagerOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.groups.filter(name="Manager").exists()

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Manager").exists()
        )

class MenuItemView(generics.ListCreateAPIView):
    permission_classes = [isManagerOrReadOnly]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price', 'featured', 'category']
    filter_backends = [OrderingFilter]

class MenuItemById(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [isManagerOrReadOnly]
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    lookup_field = 'id'

class GroupsManager(APIView):
    permission_classes = [IsManager]
    
    def get(self, request):
        managers = User.objects.filter(groups__name="Manager")
        serializer = UserSerializer(managers, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.data.get("username")
        if not user:
            return Response({"error":"username is required"},  status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            return Response({"error":"user not found"}, status=status.HTTP_404_NOT_FOUND)
        managers = Group.objects.get(name="Manager")
        managers.user_set.add(user)
        return Response({"message":f"user {user} added to the manager group"}, status=status.HTTP_201_CREATED)
    
class GroupsDeliveryCrew(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        delivery_crew = User.objects.filter(groups__name="Delivery Crew")
        serializer = UserSerializer(delivery_crew, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.data.get("username")
        if not user:
            return Response({"error":"username is required"},  status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            return Response({"error":"user not found"}, status=status.HTTP_404_NOT_FOUND)
        delivery_crew = Group.objects.get(name="Delivery Crew")
        delivery_crew.user_set.add(user)
        return Response({"message":f"user {user} added to the delivery crew group"}, status=status.HTTP_201_CREATED)

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = Cart.objects.filter(user=request.user)
        serializer = CartSerializer(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        menu_item_id = request.data.get("menu_item_id")
        quantity = request.data.get("quantity")

        if not menu_item_id or not quantity:
            return Response({"error":"menu_item_id and quantity are required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            menu_item = MenuItem.objects.get(id=menu_item_id)
        except MenuItem.DoesNotExist:
            return Response({"error":"menu item not found"}, status=status.HTTP_404_NOT_FOUND)
        
        unit_price = menu_item.price
        total_price = unit_price * int(quantity)

        cart_item, create = Cart.objects.update_or_create(
            user=request.user,
            menu_item = menu_item,
            defaults={
                "quantity": quantity,
                "unit_price": unit_price,
                "price": total_price,
            }
        )
        cart_item_serialized = CartSerializer(cart_item)
        return Response(cart_item_serialized.data, status=status.HTTP_201_CREATED)

    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_202_ACCEPTED)
    
class OrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.groups.filter(name="Manager").exists():
            orders = Order.objects.all()
            orders_serializer = OrderSerializer(orders, many=True)
            return Response(orders_serializer.data, status=status.HTTP_200_OK)
        
        if request.user.groups.filter(name="Delivery Crew").exists():
            orders = Order.objects.filter(delivery_crew__isnull=False)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        orders = Order.objects.filter(user=request.user)
        orders_serializer = OrderSerializer(orders, many=True)
        return Response(orders_serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            return Response({"detail": "your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.price for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            total=total,
            status=False,
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menu_item=item.menu_item,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )

        cart_items.delete()
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class OrderByIdView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, id=id)

        if request.user.groups.filter(name="Manager").exists():
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        if order.user != request.user:
            return Response(
                {"error": "order doesn't belong to the current user."},
                status=status.HTTP_403_FORBIDDEN
                )

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, id):
        order = get_object_or_404(Order, id=id)

        if not request.user.groups.filter(name="Manager").exists():
            return Response({"error":"unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = OrderSerializer(order, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id, *args, **kwargs):
        order = get_object_or_404(Order, id=id)

        if request.user.groups.filter(name="Delivery Crew").exists():
            serializer = OrderStatusSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user.groups.filter(name="Manager").exists():
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"error":"unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    def delete(self, request, id):
        order = get_object_or_404(Order, id=id)

        if not request.user.groups.filter(name="Manager").exists():
            return Response({"error":"unauthorized"}, status=status.HTTP_403_FORBIDDEN)
        order.delete()

        return Response({"detail":"order deleted"}, status=status.HTTP_200_OK)