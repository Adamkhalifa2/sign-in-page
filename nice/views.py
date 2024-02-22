from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, authenticate, login
from allauth.socialaccount.models import SocialAccount
from django.urls import reverse_lazy
from django.views import generic
from nice.models import Product, Item, Profile
from .forms import LoginForm

from django.contrib.auth.decorators import login_required



@login_required
def update_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.first_name = request.POST.get('first_name', '')
        profile.last_name = request.POST.get('last_name', '')
        profile.location = request.POST.get('location', '')
        profile.phone_number = request.POST.get('phone_number', '')
        profile.email = request.POST.get('email', '')
        profile.save()
        return redirect('nice:update_profile')  # Change 'welcome' to your welcome page URL name
    return render(request, 'update_profile.html')


def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('nice:welcome')
    return render(request, 'users/login.html')


def redirect_to_welcome(user):
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        return redirect('nice:welcome')
    else:
        return redirect('nice:home')


def welcome_view(request):
    if request.user.is_authenticated:
        produce = Product.objects.all()
        context = {
            'produce': produce
        }
        return render(request, 'welcome.html', context)  # Pass context as the second argument
    return redirect('nice:home')


def logout(request):
    auth_logout(request)
    return redirect('/')


class SignUpView(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy("login")
    template_name = "users/signup.html"


def cart_items(request):
    cart_items = Item.objects.filter(user=request.user)
    price = sum(item.product.price * item.quantity for item in cart_items)
    produce = Product.objects.all()

    return render(request, 'mycart.html', {'cart_items': cart_items, 'price': price})


def add_item(request, product_id):
    product = Product.objects.get(id=product_id)
    item, created = Item.objects.get_or_create(product=product, user=request.user)
    item.quantity += 1
    item.save()
    return redirect('nice:cart')


def delete_product(request, item_id):
    item = Item.objects.get(id=item_id)
    item.delete()
    return redirect('nice:cart')


def search_results(request):
    query = request.GET.get('query')
    if query:
        results = Product.objects.filter(name__icontains=query)
    else:
        results = None
    return render(request, 'search_results.html', {'results': results, 'query': query})


def increase_quantity(request, item_id):
    try:
        # Retrieve the cart item
        cart_item = Item.objects.get(id=item_id)

        # Increase the quantity by 1
        cart_item.quantity += 1
        cart_item.save()

        # Redirect back to the cart page
        return redirect('nice:cart')  # Assuming your cart URL name is 'cart'
    except Item.DoesNotExist:
        # Handle the case where the cart item does not exist
        return redirect('nice:cart')


def decrease_quantity(request, item_id):
    try:
        # Retrieve the cart item
        cart_item = Item.objects.get(id=item_id)

        # Decrease the quantity by 1 if it's greater than 1
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            # If the quantity is already 1, remove the item from the cart
            cart_item.delete()

        # Redirect back to the cart page
        return redirect('nice:cart')  # Assuming your cart URL name is 'cart'
    except Item.DoesNotExist:
        # Handle the case where the cart item does not exist
        return redirect('nice:cart')
