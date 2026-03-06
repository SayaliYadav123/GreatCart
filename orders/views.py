from functools import reduce
import json
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .forms import OrderForm
from carts.models import CartItem
import datetime
from shop.models import Product
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Order, Payment, OrderProduct


def place_order(request, total=0, quantity=0):
    current_user = request.user

    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('shop')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order':            order,
                'cart_items':       cart_items,
                'total':            total,
                'tax':              tax,
                'grand_total':      grand_total,
                'paypal_client_id': settings.PAYPAL_CLIENT_ID,
            }
            return render(request, 'orders/payments.html', context)
        else:
            return redirect('checkout')


@csrf_exempt
def payments(request):
    try:
        body = json.loads(request.body)
    except Exception as e:
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    try:
        order = Order.objects.get(
            user=request.user,
            is_ordered=False,
            order_number=body['orderID']
        )
    except Order.DoesNotExist:
        # Already processed — find the order and return so redirect works
        try:
            order = Order.objects.get(order_number=body['orderID'])
            existing_payment = Payment.objects.filter(payment_id=body['transID']).first()
            return JsonResponse({
                'order_number': order.order_number,
                'transID': existing_payment.payment_id if existing_payment else body['transID'],
            })
        except Order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        print(f'Order lookup error: {e}')
        return JsonResponse({'error': str(e)}, status=500)

    try:
        payment = Payment(
            user=request.user,
            payment_id=body['transID'],
            payment_method=body['payment_method'],
            amount_paid=order.order_total,
            status=body['status'],
        )
        payment.save()

        order.payment = payment
        order.is_ordered = True
        order.save()

        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            if OrderProduct.objects.filter(order=order, product=item.product).exists():
                continue

            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()

            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        CartItem.objects.filter(user=request.user).delete()

    except Exception as e:
        print(f'Payment processing error: {e}')
        return JsonResponse({'error': str(e)}, status=500)

    try:
        mail_subject = 'Thank you for your order!'
        message = render_to_string('orders/order_recieved_email.html', {
            'user': request.user,
            'order': order,
        })
        send_email = EmailMessage(mail_subject, message, to=[request.user.email])
        send_email.send()
    except Exception as e:
        print(f'Email failed: {e}')

    return JsonResponse({
        'order_number': order.order_number,
        'transID': payment.payment_id,
    })

def order_complete(request):
    order_number = request.GET.get('order_number')
    transID      = request.GET.get('payment_id')

    try:
        order            = Order.objects.get(order_number=order_number, is_ordered=True)
        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        payment = Payment.objects.filter(payment_id=transID).first()
        if payment is None:
            # Fallback: get payment directly from the order
            payment = order.payment

        if payment is None:
            return redirect('home')

        context = {
            'order':            order,
            'ordered_products': ordered_products,
            'order_number':     order.order_number,
            'transID':          payment.payment_id,
            'payment':          payment,
            'subtotal':         subtotal,
        }
        return render(request, 'orders/order_complete.html', context)

    except Order.DoesNotExist:
        return redirect('home')