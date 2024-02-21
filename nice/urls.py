from django.urls import path
from nice import views
from .views import SignUpView

urlpatterns = [
    path("", views.home, name='home'),  # URL for the home page
    path("welcome/", views.welcome_view, name='welcome'),  # URL for the welcome page
    path("logout/", views.logout, name='logout'),  # URL for logout
    path('signup/', SignUpView.as_view(), name='signup'),

]
