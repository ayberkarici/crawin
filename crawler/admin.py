from django.contrib import admin

# Register your models here.

from .models import *

class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'shop', 'is_best_seller', 'category_tree', 'brand_name', 'shipping_price', 'shipping_price_currency', 'created_at', 'updated_at')
    list_filter = ('shop', 'is_best_seller', 'category_tree', 'brand_name', 'shipping_price', 'shipping_price_currency', 'created_at', 'updated_at')
    search_fields = ('title', 'shop', 'is_best_seller', 'category_tree', 'brand_name', 'shipping_price', 'shipping_price_currency', 'created_at', 'updated_at')
    ordering = ('-created_at',)

class PriceAdmin(admin.ModelAdmin):
    list_display = ('product', 'first_variation_name', 'second_variation_name', 'has_variations', 'has_combinations', 'static_price', 'currency', 'created_at', 'updated_at')
    list_filter = ('product', 'first_variation_name', 'second_variation_name', 'has_variations', 'has_combinations', 'static_price', 'currency', 'created_at', 'updated_at')
    search_fields = ('product', 'first_variation_name', 'second_variation_name', 'has_variations', 'has_combinations', 'static_price', 'currency', 'created_at', 'updated_at')
    ordering = ('-created_at',)


admin.site.register(Shop)
admin.site.register(Product, ProductAdmin)
admin.site.register(Price, PriceAdmin, list_display_links=('product',))
admin.site.register(ScrapeProgress)
admin.site.register(Currency)
admin.site.register(Package)


