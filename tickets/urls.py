from django.urls import path

from tickets import views

urlpatterns = [
    path('', views.screens, name='screens'),
    path('<slug:screen_name>/', views.screen, name='screen'),
    path('<slug:screen_name>/reserve/', views.booking, name='booking'),
    path('<slug:screen_name>/seats/', views.seats, name='seats'),

]