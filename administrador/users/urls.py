from django.urls import path
from .views import LoginView, RegisterUserView, UserDetailView, LogoutView

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('profile/', UserDetailView.as_view(), name='profile'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/',LogoutView.as_view(),name= 'logout'),
]
