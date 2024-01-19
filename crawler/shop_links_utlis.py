from bs4 import BeautifulSoup
import requests
import random
from bs4 import BeautifulSoup
from .utils import *

def inspect_shop(shop_link, page_number, request):
    page_urls = []
    shop_product_link = None
    
    for i in range(0, page_number):
        page_urls.append(f'{shop_link}?page={i}')
        
        
    for idx, shop_link in enumerate(page_urls):
        product_links = []
        
        # Send the request with the provided URL, headers, and cookies
        response = get_proxied_response(shop_link)
        soup = BeautifulSoup(response, 'html.parser')
        shop_name = get_json_script(soup, "Organization")["name"].split(" - ")[0]
        
        shop, created_shop = Shop.objects.get_or_create(name=shop_name)
        
        # Get the listing urls
        for listing in soup.find_all('a', class_='listing-link'):
            clean_url = listing['href'].split("?")[0]
            product_links.append(clean_url)
            
        result_products = do_scrapping(product_links, request)
    
    return True