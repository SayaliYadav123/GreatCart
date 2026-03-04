from django.contrib import admin

# Register your models here.
class CartAdmin(admin.ModelAdmin):
    list_display=('cart_id','date_added')
class CartItemAdmin(admin.ModelAdmin):
    list_display=('product','cart','quantity','is_active')

from .models import Cart,CartItem
admin.site.register(Cart,CartAdmin)
admin.site.register(CartItem,CartItemAdmin)
