import paypalrestsdk
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout, authenticate, login
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import requests
from decimal import Decimal
from paypalrestsdk import Payment
from twilio.rest import Client
from google import settings
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
        return render(request, 'welcome.html', context)
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
        total_price = sum(Decimal(item.product.price) * item.quantity for item in cart_items)
        form = PaymentForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data['phone_number']

            # Validate the phone number
            if not phone_number:
                return HttpResponse("Please provide a phone number.")

            # Ensure phone number is in a valid format
            try:
                phone_number = int(phone_number)
            except ValueError:
                return HttpResponse("Invalid phone number format.")

            response = make_payment_api_call(total_price, phone_number)

            if response.status_code == 200:
                # Payment successful, send a notification to the specific phone number
                user = request.user
                user_profile = user.profile  # Assuming you have a UserProfile model linked to the user

                product_details = "\n".join(
                    [f"Name: {item.product.name}, Price: {item.product.price}, Description: {item.product.pdescription}"
                     for item in cart_items])

                user_info = f"User Information:\nName: {user.profile.first_name} {user.profile.last_name}\nEmail: {user.profile.email}\nLocation: {user_profile.location}"

                try:
                    send_notification("254700600163", phone_number, product_details, user_info)
                    cart_items.delete()
                    return HttpResponse("Payment successful! Notification sent.")  # You can customize this message
                except Exception as e:
                    # Handle any exception that might occur during notification sending
                    return HttpResponse(f"Payment successful, but failed to send notification: {str(e)}")
            else:
                return HttpResponse("Payment failed. Please try again.")  # You can customize this message
    else:
        form = PaymentForm()

    return render(request, 'payment_form.html', {'total_price': total_price, 'form': form})


def send_notification(receiver_phone_number, phone_number, product_details, user_info):
    account_sid = 'ACbca216ca2dd1774bf9f022f637852eb3'
    auth_token = '8c143f7a120015ac5f07e4873d725bb9'
    twilio_phone_number = '14242066602'

    client = Client(account_sid, auth_token)

    message_body = f"Client with phone number {phone_number} has made a successful payment.\n\n"
    message_body += "Product Details:\n" + product_details + "\n\n"
    message_body += user_info

    message = client.messages.create(
        body=message_body,
        from_=twilio_phone_number,
        to=receiver_phone_number
    )


def make_payment_api_call(total_price, phone_number):
    url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {
        'Authorization': 'Bearer cy60tXBHlEhuUWkeeom4VAGEBQo7',
        'Content-Type': 'application/json'
    }
    data = {
        "BusinessShortCode": 174379,
        "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU5N2RkNzFhNDY3Y2QyZTBjODkzMDU5YjEwZjc4ZTZiNzJhZGExZWQyYzkxOTIwMjQwMjE5MDg1MjAz",
        "Timestamp": "20240219085203",
        "TransactionType": "CustomerPayBillOnline",
        "Amount": total_price,
        "PartyA": 254700600163,
        "PartyB": 174379,
        "PhoneNumber": phone_number,
        "CallBackURL": "https://mydomain.com/path",
        "AccountReference": "CompanyAdam",
        "TransactionDesc": "Payment ADAM"
    }
    response = requests.post(url, headers=headers, json=data)
    return response


def payment(request):
    if request.method == 'POST':

        cart_items = Item.objects.filter(user=request.user)

        total_price = sum(item.product.price * item.quantity for item in cart_items)

        ksh_to_usd_rate = Decimal('0.0093 ')

        usd_total_price = total_price * ksh_to_usd_rate

        usd_total_price_str = '{:.2f}'.format(usd_total_price)

        paypal_client_id = settings.PAYPAL_CLIENT_ID
        paypal_client_secret = settings.PAYPAL_CLIENT_SECRET
        paypal_mode = settings.PAYPAL_MODE

        paypalrestsdk.configure({
            "mode": paypal_mode,
            "client_id": paypal_client_id,
            "client_secret": paypal_client_secret
        })

        payment = Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": "http://127.0.0.1:8000/payment/execute/",
                "cancel_url": "http://127.0.0.1:8000/payment/cancel/"
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": "Item",
                        "sku": "item",
                        "price": usd_total_price_str,
                        "currency": "USD",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": usd_total_price_str,
                    "currency": "USD"
                },
                "description": "Payment for items."
            }]
        })

        if payment.create():
            request.session['payment_id'] = payment.id
            for link in payment.links:
                if link.method == 'REDIRECT':
                    redirect_url = str(link.href)
                    return redirect(redirect_url)
        else:
            return HttpResponse("Payment creation failed. Please try again.")

    return render(request, 'payment.html')
