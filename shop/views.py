from django.shortcuts import render
from http.client import HTTPResponse
from itertools import product
from django.db.models import Q
from django.conf import settings
from django.shortcuts import render, get_object_or_404,redirect
from shop.models import Product, ReviewRating, ProductGallery
from django.http import HttpResponse,JsonResponse
from .models import Product
from category.models import Category,Gender
from carts.models import CartItem
from shop.models import ReviewRating
from carts.views import _cart_id
from django.core.paginator import Paginator
from .forms import ReviewForm
from django.contrib import messages
from orders.models import OrderProduct
# Create your views here.
def shop(request):
    return render(request, 'store/shop.html', {
        'all_genders': Gender.objects.all(),
    })



def product_display(request, gender_slug):
    gender     = get_object_or_404(Gender, slug=gender_slug)
    categories = Category.objects.filter(gender=gender)

    return render(request, 'store/productDisplay.html', {
        'gender':      gender,
        'categories':  categories,
        'all_genders': Gender.objects.all(),
    })


# ─────────────────────────────────────────────────────────
# AJAX — called when user clicks a category pill
# URL: /store/men/products/?category=shirts
#      /store/men/products/              ← all men products
# Returns JSON, no page reload
# ─────────────────────────────────────────────────────────
def load_products(request, gender_slug):
    category_slug = request.GET.get('category', 'all')
    gender = get_object_or_404(Gender, slug=gender_slug)

    if category_slug and category_slug != 'all':
        category = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(gender=gender, category=category)
    else:
        products = Product.objects.filter(gender=gender)

    product_list = []
    for p in products:
        product_list.append({
            'id': p.id,
            'name': p.product_name,
            'price': p.price,
            'image': p.images.url if p.images else '',
            'stock': p.stock,
            'category': str(p.category),
            # ↓ Build the full URL with all 3 slugs
            'url': f'/shop/{gender_slug}/{p.category.slug}/{p.slug}/',
        })

    return JsonResponse({'products': product_list})


# ─────────────────────────────────────────────────────────
# PRODUCT DETAIL
# URL: /store/men/shirts/blue-shirt/
# Only reached by clicking a product card
# ─────────────────────────────────────────────────────────
def product_detail(request, gender_slug, category_slug, product_slug):
    gender   = get_object_or_404(Gender,   slug=gender_slug)
    category = get_object_or_404(Category, slug=category_slug, gender=gender)

    product  = get_object_or_404(Product,  slug=product_slug,  category=category)

    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    except Exception as e:
        raise e

    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    # Get the reviews
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    # Get the product gallery
    product_gallery = ProductGallery.objects.filter(product_id=single_product.id)

    in_cart = CartItem.objects.filter(
        cart__cart_id=_cart_id(request),
        product=product
    ).exists()

    return render(request, 'store/product_detail.html', {
        'single_product': product,
        'in_cart':        in_cart,
        'orderproduct': orderproduct,
        'reviews': reviews,
        'product_gallery': product_gallery,
    })


import os
import uuid
import base64
import json
import requests
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

# Import your existing API function
from shop.utils.api4ai import call_tryon_api   # adjust import path as needed


# @login_required
@require_POST
def tryon_ajax(request):
    try:
        body = json.loads(request.body)
        user_photo_b64 = body.get("user_photo")      # data:image/jpeg;base64,....
        product_image_url = body.get("product_image") # absolute or relative URL
        product_id = body.get("product_id")

        if not user_photo_b64 or not product_id:
            return JsonResponse({"success": False, "error": "Missing photo or product_id"})

        # ── 1. Save user photo to a temp file ──────────────────────────
        temp_dir = os.path.join(settings.MEDIA_ROOT, "tryon_temp")
        os.makedirs(temp_dir, exist_ok=True)

        uid = uuid.uuid4().hex[:10]

        # Strip the data-URL header  (data:image/jpeg;base64,...)
        if "," in user_photo_b64:
            header, b64data = user_photo_b64.split(",", 1)
        else:
            b64data = user_photo_b64

        person_path = os.path.join(temp_dir, f"person_{uid}.jpg")
        with open(person_path, "wb") as f:
            f.write(base64.b64decode(b64data))

        # ── 2. Save cloth/product image to a temp file ─────────────────
        cloth_path = os.path.join(temp_dir, f"cloth_{uid}.jpg")

        # If the product image is a URL (http/https), download it
        if product_image_url.startswith("http"):
            img_response = requests.get(product_image_url, timeout=30)
            img_response.raise_for_status()
            with open(cloth_path, "wb") as f:
                f.write(img_response.content)
        else:
            # It's a relative media URL — resolve to local path
            relative = product_image_url.lstrip("/")
            # Strip MEDIA_URL prefix if present
            media_prefix = settings.MEDIA_URL.lstrip("/")
            if relative.startswith(media_prefix):
                relative = relative[len(media_prefix):]
            local_cloth = os.path.join(settings.MEDIA_ROOT, relative)
            print("🔍 Looking for cloth image at:", local_cloth)
            if not os.path.exists(local_cloth):
                print("❌ CLOTH FILE NOT FOUND:", local_cloth)
                return JsonResponse({"success": False, "error": "Product image not found on server"})
            import shutil
            shutil.copy(local_cloth, cloth_path)
            print("✅ Cloth image copied successfully")

        # ── 3. Call the API4AI try-on ───────────────────────────────────
        result = call_tryon_api(
            person_path=person_path,
            cloth_path=cloth_path,
            product_id=product_id,
            user=request.user
        )

        # ── 4. Cleanup temp files ───────────────────────────────────────
        for p in [person_path, cloth_path]:
            try:
                os.remove(p)
            except Exception:
                pass

       
        if result:
            result_url = request.build_absolute_uri(result.result_image_url)
            print("✅ Returning result_url:", result_url)
            return JsonResponse({"success": True, "result_url": result_url})
   
    
        else:
            print("❌ call_tryon_api returned None")
            return JsonResponse({"success": False, "error": "Try-on API returned no result"})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"success": False, "error": str(e)})
    

def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
