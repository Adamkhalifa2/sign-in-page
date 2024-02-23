from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, authenticate, login
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
import requests
from decimal import Decimal

from .forms import PaymentForm
from .models import Product, Item, Profile
from allauth.socialaccount.models import SocialAccount

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
        return redirect('nice:update_profile')
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
        products = Product.objects.all()
        context = {
            'products': products
        }
        return render(request, 'welcome.html', context )
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
    formatted_price = "{:.2f}".format(price)  # Format the price with two decimal places
    products = Product.objects.all()
    return render(request, 'mycart.html', {'cart_items': cart_items, 'price': formatted_price, 'products': products})


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
        cart_item = Item.objects.get(id=item_id)
        cart_item.quantity += 1
        cart_item.save()
        return redirect('nice:cart')
    except Item.DoesNotExist:
        return redirect('nice:cart')


def decrease_quantity(request, item_id):
    try:
        cart_item = Item.objects.get(id=item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
        return redirect('nice:cart')
    except Item.DoesNotExist:
        return redirect('nice:cart')


def make_payment(request):
    total_price = Decimal(0)
    if request.method == 'POST':
        cart_items = Item.objects.filter(user=request.user)
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        form = PaymentForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']

            # Validate the phone number
            if not phone_number:
                return HttpResponse("Please provide a phone number.")

            try:
                phone_number = int(phone_number)
            except ValueError:
                return HttpResponse("Invalid phone number format.")

            # Call your payment API with the provided data
            response = make_payment_api_call(float(total_price), phone_number)

            # Check the response from the API and handle accordingly
            if response.status_code == 200:
                # Clear the cart items after successful payment
                cart_items.delete()

                return HttpResponse("Payment successful!")  # You can customize this message
            else:
                return HttpResponse("Payment failed. Please try again.")  # You can customize this message
    else:
        form = PaymentForm()

    return render(request, 'payment_form.html', {'total_price': total_price, 'form': form})
def make_payment_api_call(total_price, phone_number):
    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': 'Bearer h1PIG1vJa3k3Gq7d6QNu5ntYhJTj',  # Replace with your actual access token
        'Content-Type': 'application/json'
    }
    data = {
        "BusinessShortCode": 174379,
        "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU5N2RkNzFhNDY3Y2QyZTBjODkzMDU5YjEwZjc4ZTZiNzJhZGExZWQyYzkxOTIwMjQwMjE5MDg1MjAz",
        "Timestamp": "20240219085203",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": total_price,  # Corrected from amount to total_price
        "PartyA": 254700600163,
        "PartyB": 174379,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://mydomain.com/path",
        "AccountReference": "CompanyAdam",
        "TransactionDesc": "Payment ADAM"
    }
    response = requests.post(url, headers=headers, json=data)
    return response


def send_payment_notification(email, amount):
    subject = 'Payment Notification'
    message = f'Your payment of ${amount} has been successfully processed.'
    from_email = 'your_email@example.com'  # Your email address
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)
