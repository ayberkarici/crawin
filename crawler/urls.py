from django.urls import path

from . import views

app_name = 'crawler'
urlpatterns = [
    path('', views.index, name='index'),
    path('shop_crawler/', views.shop_crawler, name='shop_crawler'),
    path('process-scrapping/', views.process_scrapping, name='process_scrapping'),
    path('process-shop-scrapping/', views.process_shop_scrapping, name='process_shop_scrapping'),
    path('export_package/<uuid:package_uuid>/', views.export_package_to_excel, name='export_package_to_excel'),
    
    
]