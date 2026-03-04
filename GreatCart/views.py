from django.shortcuts import render





from django.shortcuts import render
from django.core.paginator import Paginator
from django.shortcuts import render
from shop.models import Product
from category.models import Gender


def home(request):
    products = Product.objects.filter(is_available=True).order_by('-created_date')
    all_genders = Gender.objects.all()

    # Pagination — 12 products per page
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products = paginator.get_page(page)

    context = {
        'products': products,
        'all_genders': all_genders,
    }
    return render(request, 'home.html', context)

def about(request):
    
    return render(request, 'about.html')

