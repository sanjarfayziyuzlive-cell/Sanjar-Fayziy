from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('konspekt/yozish/', views.yozish, name='yozish'),
    path('konspekt/<int:pk>/', views.detail, name='detail'),
    path('konspekt/<int:pk>/tahrirlash/', views.tahrirlash, name='tahrirlash'),
    path('konspekt/<int:pk>/ochirish/', views.ochirish, name='ochirish'),
    path('konspekt/<int:pk>/layk/', views.like, name='like'),
    path('konspekt/<int:pk>/izoh/', views.comment, name='comment'),
    path('konspekt-preview/', views.preview, name='konspekt_preview'),
]
