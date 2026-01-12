from django.urls import path, include
from . import views

urlpatterns = [
    path('menu-items/', views.MenuItemView.as_view()),
    path('menu-items/<int:id>', views.MenuItemById.as_view()),
    path('groups/manager/users/', views.GroupsManager.as_view()),
    path('cart/menu-items/', views.CartView.as_view()),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:id>', views.OrderByIdView.as_view()),
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
]