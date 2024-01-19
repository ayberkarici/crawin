from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from .utils import *
import uuid 
from .models import *
from .shop_links_utlis import *
from django.http import HttpResponse
import pandas as pd
from openpyxl import Workbook

# Create your views here.

@login_required
def index(request):
    return render(request, 'crawler/index.html')

@login_required
def shop_crawler (request):
    packages = Package.objects.filter(user=request.user)
    
    
    for package in packages:
        if package.products.count() == 0:
            package.delete()
            continue
        
        if package.shop_name == None: 
            try: 
                package.shop_name = package.products.first().shop.name
                package.save()
            except:
                package.delete()
    
    context = {
        "packages": packages,
    }
    
    return render(request, 'crawler/shop_crawler.html', context)

@login_required
@require_POST
def process_scrapping(request):
    shop_links = request.POST.getlist('shop_links[]')
    
    # Do scrapping process here
    
    for shop_link in shop_links:
        if is_string_an_url(shop_link):
            print('Valid URL!')
        else:
            print('Invalid URL!')
            return JsonResponse({'status': 'error', 'message': f'Invalid URL! - {shop_link}'})

    # Create a new ScrapeProgress object
    scrape_progress = ScrapeProgress.objects.get_or_create(task_id=uuid.uuid4().hex, progress=0.0)
    
    process = do_scrapping(shop_links, request)
    
    if process:
        # Save the scrape_progress object
        return JsonResponse({'status': 'success', 'message': 'Scrapping process ended succesfuly!'})
    
    # Return a json response
    return JsonResponse({'status': 'success', 'message': 'Something went wrong!'})

@login_required
@require_POST
def process_shop_scrapping(request):
    shop_link = request.POST.get('shop_link')
    shop_link = shop_link.split("?")[0]
    
    shop_page_number = request.POST.get('shop_page_number')
    
    
    # Check if shop_page_number is a integer
    if not is_string_an_integer(shop_page_number):
        return JsonResponse({'status': 'error', 'message': 'Shop page number must be an integer!'})
    
    if is_string_an_url(shop_link):
        print('Valid URL!')
    else:
        print('Invalid URL!')
        return JsonResponse({'status': 'error', 'message': f'Invalid URL! - {shop_link}'})
    
    # Create a new ScrapeProgress object
    scrape_progress, created = ScrapeProgress.objects.get_or_create(task_id=uuid.uuid4().hex, progress=0.0)
    
    process_shop = inspect_shop(shop_link, int(shop_page_number), request)
    
    if process_shop:
        # Return a json response
        return JsonResponse({'status': 'success', 'message': 'Shop found!'})
    
    # Return a json response
    return JsonResponse({'status': 'error', 'message': 'Shop not found!'})


def export_package_to_excel(request, package_uuid):
    # Retrieve the specific Package instance and related Product instances
    package = Package.objects.get(uuid=package_uuid)
    products = package.products.all()

    # Create a list of dictionaries with the data you want to export
    data = []
    for product in products:
        price = Price.objects.filter(product=product).order_by('-created_at').first()
        
        product_data = {
            'Title': product.title,
            'Description': product.description,
            'Tags': ', '.join(product.tags),  # Convert tags list to a string
            'Images': ', '.join(product.images),  # Convert images list to a string
            'Is Best Seller': product.is_best_seller,
            'Category Tree': product.category_tree,
            'URL': product.url,
            'Brand Name': product.brand_name,
            'Shipping Price': product.shipping_price,
            'Shipping Price Currency': product.shipping_price_currency,
            'First Variation Name': price.first_variation_name,
            'Second Variation Name': price.second_variation_name,
            'First Variation Values': price.first_variation_values,
            'Second Variation Values': price.second_variation_values,
            'Has Variations': price.has_variations,
            'Has Combinations': price.has_combinations,
            'Static Price': price.static_price,
            'Combination Prices': price.combination_prices,
            'Currency': price.currency,
        }
        data.append(product_data)

    # Create a Pandas DataFrame from the list of dictionaries
    df = pd.DataFrame(data)

    # Create an Excel writer object
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename=package_{package_uuid}.xlsx'
    writer = pd.ExcelWriter(response, engine='openpyxl')  # Add 'options' to remove timezone info

    # Convert the DataFrame to an Excel sheet
    df.to_excel(writer, index=False, sheet_name='Package Data')

    # Close the writer to save the content to the HttpResponse
    writer.close()

    # Return the HttpResponse
    return response

