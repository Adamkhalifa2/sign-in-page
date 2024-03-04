import paypalrestsdk
from django.contrib.auth.forms import UserCreationForm
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
from .models import Product, Item, Profile, Profiles
from allauth.socialaccount.models import SocialAccount
from django.shortcuts import render, redirect, get_object_or_404
from nice.forms import ProfilesForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import UserRegistrationForm


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
    return render(request, 'update_profile.html', {'profile': profile})


def contact_us(request):
    return render(request, 'contact_us.html')


def home(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # If the user exists and the password is correct, log in the user
            login(request, user)
            return redirect('nice:welcome')
        else:
            # If the provided credentials are invalid, display an error message
            error_message = "Invalid username or password."
            return render(request, 'users/login.html', {'error_message': error_message})
    return render(request, 'users/login.html')


def redirect_to_welcome(user):
    if SocialAccount.objects.filter(user=user, provider='google').exists():
        return redirect('nice:welcome')
    else:
        return redirect('nice:home')


def welcome_view(request):
    if request.user.is_authenticated:
        products = Product.objects.all()
        profiles = Profile.objects.all()
        context = {
            'products': products,
            'profiles': profiles
        }
        return render(request, 'welcome.html', context)
    return redirect('nice:home')


def logout(request):
    auth_logout(request)
    return redirect('/')


def register(request):
    profile = None

    if request.user.is_authenticated:
        return redirect("/")

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            profile = Profiles.objects.create(user=user)

            # Log in the user
            login(request, user)

            return redirect('nice:add_profile_photo')
        else:
            for error in form.errors.values():
                print(request, error)
    else:
        form = UserRegistrationForm()

    return render(
        request=request,
        template_name="register.html",
        context={"form": form, "profile": profile}
    )


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
    try:
        item = get_object_or_404(Item, id=item_id, user=request.user)
        item.delete()
        return redirect('nice:cart')
    except Item.DoesNotExist:
        return HttpResponse("Item does not exist.")


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

                # Calculate the number of items and identify duplicates
                num_items = sum(item.quantity for item in cart_items)
                duplicates = [item.product.name for item in cart_items if item.quantity > 1]

                if duplicates:
                    duplicate_message = f"Products added more than once: {', '.join(duplicates)}"
                else:
                    duplicate_message = "No products added more than once."

                try:
                    send_notification("+254700600163", phone_number, product_details, user_info, num_items, total_price,
                                      duplicate_message)
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


def send_notification(receiver_phone_number, phone_number, product_details, user_info, num_items, total_price, duplicate_message):
    account_sid = 'ACbca216ca2dd1774bf9f022f637852eb3'
    auth_token = '26506fc36826a930914a2d1ad09afa23'
    twilio_phone_number = '+14242066602'

    client = Client(account_sid, auth_token)

    message_body = f"Client with phone number {phone_number} has made a successful payment.\n\n"
    message_body += f"Number of items: {num_items}\n"
    message_body += f"Total price: kes {total_price}\n\n"
    message_body += f"Products added more than once: {duplicate_message}\n\n"
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
        'Authorization': 'Bearer xIFBewUAS8aALO4oP5iwmANb3vvO',
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


def add_profile_photo(request):
    # Check if the user already has a profile picture
    existing_profile = get_object_or_404(Profiles, user=request.user)

    if request.method == 'POST':
        profile_form = ProfilesForm(request.POST, request.FILES, instance=existing_profile)
        if profile_form.is_valid():
            profile = profile_form.save()
            return redirect('nice:welcome')
    else:
        profile_form = ProfilesForm(instance=existing_profile)

    return render(request, 'add_profile_photo.html', {'profile_form': profile_form})
