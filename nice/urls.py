from django.urls import path
from nice import views
from .views import SignUpView

app_name = 'nice'

urlpatterns = [
    path("", views.home, name='home'),  # URL for the home page
    path("welcome/", views.welcome_view, name='welcome'),  # URL for the welcome page
    path("logout/", views.logout, name='logout'),  # URL for logout
    path('signup/', SignUpView.as_view(), name='signup'),
    path("cart/", views.cart_items, name='cart'),
    path("add/<int:product_id>/", views.add_item, name='add'),
    path("delete/<int:item_id>/", views.delete_product, name='delete'),
    path('search/', views.search_results, name='search_results'),
    path('decrease_quantity/<int:item_id>/', views.decrease_quantity, name='decrease_quantity'),
    path('increase_quantity/<int:item_id>/', views.increase_quantity, name='increase_quantity'),
    path('update-profile/', views.update_profile, name='update_profile'),
    path('make-payment', views.make_payment, name='make_payment'),
    path('payment/', views.payment, name='payment'),
]
