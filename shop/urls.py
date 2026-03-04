from django.urls import path
from . import views

from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [

    # /store/                          ← Navbar "Shop" button
    path('',
         views.shop,
         name='shop'),
     path('tryon-ajax/', views.tryon_ajax, name='tryon_ajax'),

    # /store/men/                      ← Home "Men" button OR Shop page "Men" card
    # /store/women/                    ← Home "Women" button OR Shop page "Women" card
    path('<slug:gender_slug>/',
         views.product_display,
         name='product_display'),

    # /store/men/products/?category=shirts   ← AJAX only, returns JSON
    path('<slug:gender_slug>/products/',
         views.load_products,
         name='load_products'),

    # /store/men/shirts/blue-shirt/    ← clicking a product card
    path('<slug:gender_slug>/<slug:category_slug>/<slug:product_slug>/',
         views.product_detail,
         name='product_detail'),

         

]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

