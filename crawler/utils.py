from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
import requests
from bs4 import BeautifulSoup
import json
import random
import pprint 
from .models import *


# # HANDLING FUNCTIONS
# def get_proxied_response(url):
    
#     cookie_file = "./cookies.txt"  # Cookie'lerin kaydedileceği dosya
    
#     def load_cookies():
#         try:
#             with open(cookie_file, 'r') as file:
#                 cookies = {}
#                 for line in file:
#                     name, value = line.strip().split('\t')
#                     cookies[name] = value
#                 return cookies
#         except FileNotFoundError:
#             return {}

#     def save_cookies(cookies):
#         with open(cookie_file, 'w') as file:
#             for name, value in cookies.items():
#                 file.write(f"{name}\t{value}\n")
                

#     cookies = load_cookies()  # Kaydedilmiş cookie'leri yükle
                
#     # Generate a random User-Agent
#     user_agents = [
#         "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0"
#         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36"
#         "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.130 Safari/537.36"
#     ]
    
#     user_agent = random.choice(user_agents)
    
#     # Set the User-Agent header
#     headers = {
#         'User-Agent': user_agent,
#         'accept-language': 'en-GB,en;q=0.9'
#     }


#     # Send the request with the provided URL, headers, and cookies
#     response = requests.get(url, headers=headers, cookies=cookies)
#     print("Response status code: ", response.status_code)
        
#     if response.status_code != 200:
#         raise Exception(f'Failed to load page {url}')
      
#     # Update the cookies with the new ones received in the response
#     cookies.update(response.cookies.get_dict())

#     # Save the updated cookies for future use
#     save_cookies(cookies)
    
#     if response.status_code != 200:
#         raise Exception(f'Failed to load page {url}')
    
#     return response.content

def get_proxied_response(url):
    payload = { 'api_key': '0557e7dfa1d11ce17d1dcaf1c60719be', 'url': url, 'follow_redirect': False, 'country_code': 'us', 'device_type': 'desktop', 'session_number': 1 } 
    r = requests.get('https://api.scraperapi.com/', params=payload)
    
    return r.text

def do_scrapping(item_links, request):    
    print("Getting started...")
    result = []
    result = start_scrapping(item_links, request)
    
    return result

def start_scrapping(item_links, request):    
    instances = []
    
    package = Package.objects.create(user=request.user)

    for shop_link in item_links:
        global price_data
        global product_data
        global product_instance
        
        print(f"Scrapping the url: {shop_link}")
        
        if '?' in shop_link:
            clear_url = shop_link.split('?')[0]
        else:    
            clear_url = shop_link
            
        # Do scrapping process here
        response = get_proxied_response(clear_url)
        soup = BeautifulSoup(response, 'html.parser')
        
        product_schema = get_json_script(soup, "Product")
        
        try: 
            shop, created = Shop.objects.get_or_create(name=product_schema['brand']['name'])
        except:
            return False
        
        
        product_data = {
            "shop" : shop,
            "title" : product_schema['name'],
            "description" : product_schema['description'],
            "tags" : get_tags(soup),
            "images" : get_images(soup),
            "is_best_seller" : is_bestseller(soup),
            "category_tree" : product_schema['category'],
            "url" : product_schema['url'],
            "brand_name" : product_schema['brand']['name'],
            "shipping_price" : get_shipping_price(soup)[0],
            "shipping_price_currency" : get_shipping_price(soup)[1],
        }
        
        price_data = {
            "first_variation_name" : "",
            "second_variation_name" : "",
            "first_variation_values" : {},
            "second_variation_values" : {},
            "has_variations" : 0,
            "has_combinations" : 0,
            "static_price" : 0.0,
            "combination_prices" : {},
            "currency" : "",
        }
        
        # print(json.dumps(product_schema, indent=2))

        # Pricing algorithms
        status = set_the_prices(soup, clear_url)
        
        if status:
            print("Product saved succesfully!")
            instances.append(product_instance)
            print("product_instance -> ", product_instance)
            
            # Check if the package has the product
            if not package.products.filter(id=product_instance.id).exists():
                package.products.add(product_instance)
            else: 
                print("This product already exists in this package!")
                
        else: 
            print("Something went wrong with this url ->", clear_url)
            
    package.save()
        
    return instances


# PRICING ALGORITHM
def set_the_prices(soup, url):
    print("Getting the prices...")
    
    prices = []
    
    # Find all select elements with class 'wt-select__element' and has attribute 'data-variation-number' ==> Variations 
    selects = soup.find_all('select', {'class': 'wt-select__element', 'data-variation-number': True})
    
    # Check if there are options 
    ####### PRICING ALGORITHM #######
    if len(selects) == 0:
        print("No options. Taking only the price...", )

        product_json = get_json_script(soup, "Product")
        primary_price = product_json['offers']['price']
        price_currency = product_json['offers']['priceCurrency']
        
        price_data["currency"] = price_currency
        price_data["static_price"] = primary_price
        
        status = save_product_with_price()
        
        return status
        
    elif len(selects) == 1:
        print("1 tane option var. Varyasyonlar kontrol ediliyor...")
        extracted_prices = []
        
        # If there is only one select element, process it
        reference_select_tag = selects[0]
        
        # Find the data-label in the soup and get the text
        label_name = soup.find('span', {'data-label': True}).get_text().strip()

        # Check if there is a price in the options
        has_price = check_if_option_has_price(reference_select_tag)
        
        product_json = get_json_script(soup, "Product")
    
        # Save the data to the price_data dictionary
        price_data["first_variation_name"] = label_name
        price_data["has_variations"] = 1
        
        if has_price:
            print("There is a price in the options. Taking the prices...")
            primary_price = None
            
        else:      
            print("There is no price in the options. Taking the main price as reference...")
            primary_price = product_json['offers']['price'] 
        
        price_currency = product_json['offers']['priceCurrency']
        extracted_prices = process_one_select_element_nonpriced(reference_select_tag, primary_price, price_currency, label_name)
        
        if extracted_prices:
            status = save_product_with_price()
            return status
        
        return False
            
    elif len(selects) == 2:
        # If there are options, check if there are more than one select element
        print("2 tane option var. Hangileri gerekli araştırılıyor...")

        # If there are two select elements, check if there is a price in both select elements
        has_select_priced = check_if_options_has_price(selects)
        
        # Find the data-label in the soup and get the text
        label_names = soup.find_all('span', {'data-label': True})
        
        # Get the currency of the product
        product_json = get_json_script(soup, "Product")
        price_currency = product_json['offers']['priceCurrency']
        
        first_label = label_names[0].get_text().strip()
        second_label = label_names[1].get_text().strip()
        
        price_data["first_variation_name"] = first_label
        price_data["second_variation_name"] = second_label
        price_data["has_variations"] = 1
        price_data["currency"] = price_currency
        
        
        if has_select_priced[0] and has_select_priced[1]:
            print("There are prices in both select elements. Taking the prices...")
            
            # MINIMUM OPTIONS RULE
            refrence_number = decide_reference_element(selects)
            
            price_data["has_combinations"] = 1
            
            reference_element = selects[refrence_number]
            reference_select_tag_number = refrence_number
            status = process_variation_pages(url, reference_element, reference_select_tag_number)
            
            if status:
                status = save_product_with_price()
                return status
            
        elif has_select_priced[0] and not has_select_priced[1]:
            print("There is a price in the first select element. Taking the prices...")
            
            price_data["has_combinations"] = 1
            
            reference_element = selects[0]
            reference_select_tag_number = 0
            status = process_variation_pages(url, reference_element, reference_select_tag_number)
            
            if status:
                status = save_product_with_price()
                return status
                
        elif not has_select_priced[0] and has_select_priced[1]:
            print("There is a price in the second select element. Taking the prices...")
            
            price_data["has_combinations"] = 1
            
            reference_element = selects[1]
            reference_select_tag_number = 1
            status = process_variation_pages(url, reference_element, reference_select_tag_number) 

            if status:  
                status = save_product_with_price()
                return status
            
        else:
            print("There is no price in both select elements. Taking the main price as reference...")
            reference_element = selects[1]
            reference_select_tag_number = 1
            status = process_variation_pages_nonpriced(soup)
            
            if status:
                status = save_product_with_price()
                return status
            
        return status
            
def remove_text_between_parentheses(text):
    if check_if_text_has_price(text):        
        last_close_parenthesis_index = text.rfind(")")
        if last_close_parenthesis_index != -1:
            before_last_open_parenthesis_index = text.rfind("(", 0, last_close_parenthesis_index)
            if before_last_open_parenthesis_index != -1:
                return text[:before_last_open_parenthesis_index] + text[last_close_parenthesis_index+1:] , text[before_last_open_parenthesis_index:last_close_parenthesis_index+1]
        return text.trim(), ""

def check_if_option_has_price(select_tag):
    has_price = False
    
    # Process each option element in the select element variation X
    for variation_option in select_tag.find_all('option'):
        # Values and text of the option for variation X
        variation_text = variation_option.get_text().strip()
        
        if check_currency_in_text(variation_text):
            print("There is a price in the options.")
            has_price = True
            break
        
    return has_price

def process_one_select_element_nonpriced(select_tag, primary_price, price_currency, label):
    options = {}
    price_data["static_price"] = primary_price
    price_data["currency"] = price_currency
    price_data["first_variation_name"] = label
    price_data["second_variation_name"] = ""
    price_data["has_variations"] = 1

    # Process each option element in the select element variation X
    for variation_option in select_tag.find_all('option'):
        # Values and text of the option for variation X
        variation_text = variation_option.get_text().strip()
        
        if 'Select' in variation_text:
            continue
        
        options[variation_option.get('value').strip()] = variation_text
        
        
    price_data["first_variation_values"] = options
        
    return True

def check_if_options_has_price(select_tags):
    has_price = [0, 0]
    
    # Select elementlerindeki optionların içinde fiyat var mı kontrol ediliyor
    for idx, select_tag in enumerate(select_tags):
        for variation_option in select_tag.find_all('option'):
            variation_text = variation_option.get_text().strip()
            has_price[idx] = False
            
            if check_currency_in_text(variation_text):
                has_price[idx] = True
                break
            
    return has_price

def check_if_text_has_price(text):
    has_price = False
    
    if check_currency_in_text(text):
        has_price = True
        
    return has_price

def decide_reference_element(select_tags):
    first_select_tag_counter = 0
    second_select_tag_counter = 0
    refrence_number = None

    # Select elementlerindeki optionların içinde fiyat var mı kontrol ediliyor
    for idx, select_tag in enumerate(select_tags):
        for variation_option in select_tag.find_all('option'):
            variation_text = variation_option.get_text().strip()
            
            if 'Select' in variation_text:
                continue
            
            if check_currency_in_text(variation_text):
                if idx == 0:
                    first_select_tag_counter += 1
                else:
                    second_select_tag_counter += 1
            
    if first_select_tag_counter < second_select_tag_counter :
        refrence_number = 0
    else:
        refrence_number = 1
        
    return refrence_number

def process_variation_pages(url, reference_element, reference_select_tag_number):
    reference_option_values = []
    
    for option in reference_element.find_all('option'):
        text = option.get_text().strip()
        
        # Check for brackets in the option text and add to options list
        if check_currency_in_text(text):
            variation_selected_option_value = option.get('value').strip()
            reference_option_values.append(variation_selected_option_value)
        
        
    for reference_option_value in reference_option_values:
        updated_url = f"{url}?variation{reference_select_tag_number}={reference_option_value}"
        
        print("Scrapping reference options..." , updated_url)
        
        response = get_proxied_response(updated_url)
        
        soup = BeautifulSoup(response, 'html.parser')
        
        # Find all select elements with class 'wt-select__element' and has attribute 'data-variation-number' ==> Variations
        selects = soup.find_all('select', {'class': 'wt-select__element', 'data-variation-number': True})
        
        # Select the variation element which is not the reference element
        if reference_select_tag_number == 0:
            variation_select_tag = selects[1]
        else:
            variation_select_tag = selects[0]
            
        for option in reference_element.find_all('option'):
            text = option.get_text().strip()
            if option.get('value').strip() == reference_option_value:
                reference_selected_text = text
                break
        
        status = process_select_elements(variation_select_tag, reference_selected_text)

    return status

def process_select_elements(variation_select_element, reference_text):
    """
    Burada sistem şu şekilde çalışıyor:
    1. Gelen select elementlerinden içinde variation_selected_option_value değerine sahip olan select elementi seçiliyor
    2. Seçili olan select elementindeki variation_selected_option_value değerine sahip olan option seçiliyor
    3. Seçili olan optionun text değeriyle diğer select elementindeki optionların text değerleri kombine ediliyor
    4. 3. adımda oluşan text değerleri prices listesine ekleniyor
    """

    if 'Select' in reference_text:
        return True

    prices = []
    
    # Find all option elements in the select element variation X    
    variations_options = variation_select_element.find_all('option')
    
    # Process each option element in the select element variation X
    for variation_option in variations_options:
        # Values and text of the option for variation X
        variation_text = variation_option.get_text().strip()
        
        if 'Select' in variation_text:
            continue
        
        prices.append(variation_text) 

    price_data["combination_prices"][reference_text] = prices
        
    return True

def process_variation_pages_nonpriced(soup):
    # Find all select elements with class 'wt-select__element' and has attribute 'data-variation-number' ==> Variations
    selects = soup.find_all('select', {'class': 'wt-select__element', 'data-variation-number': True})
    
    product_json = get_json_script(soup, "Product")
    primary_price = product_json['offers']['price']
    price_currency = product_json['offers']['priceCurrency']
    
    price_data["static_price"] = primary_price
    price_data["currency"] = price_currency
    
    try:    
        for idx, select in enumerate(selects):
            for option in select.find_all('option'):
                text = option.get_text().strip()
                
                if 'Select' in text:
                    continue
                
                if idx == 0:
                    price_data["first_variation_values"][option.get('value').strip()] = text
                else: 
                    price_data["second_variation_values"][option.get('value').strip()] = text
                    
    except:
        return False
                    
    return True

    
# GENERAL PRODUCT DETAILS ALGORITHM
def get_images(soup):
    images = []
    
    try:
        for img in soup.find_all('img', {'class': 'wt-max-width-full wt-horizontal-center wt-vertical-center carousel-image wt-rounded'}):
            images.append(img['src'])
    except:
        images = []
        
    return images

def get_tags(soup):
    tags = []
        
    # get the last div element with class 'recs-appears-logger'
    div_element = soup.find_all('div', {'class': 'recs-appears-logger'})[-1]
    
    # 'data-appears-event-data' attribute'ünü JSON'a çevir ve 'queries' anahtarını al
    if div_element:
        event_data = json.loads(div_element['data-appears-event-data'])
        tags = event_data.get("queries", [])[:13]  # İlk 13 query
        
    return tags

def is_bestseller(soup):
    # aria-describedby="bestseller"
    is_bestseller = False
    
    try:
        if soup.find('button', {'aria-describedby=':'bestseller'}):
            is_bestseller = True
        else:
            is_bestseller = False
    except:
        is_bestseller = False
    
    return is_bestseller

def get_shipping_price(soup):
    # 'data-selector' değeri 'shipping-highlights' olan div bulunuyor
    shipping_div = soup.find('div', attrs={'data-selector': 'shipping-highlights'})
    
    # 'currency-symbol' class'ına sahip bir span var mı kontrol ediliyor
    currency_symbol_span = shipping_div.find('span', class_='currency-symbol')
    
    # Eğer varsa, sembol ve value alınıyor
    if currency_symbol_span:
        currency_symbol = currency_symbol_span.text.strip()
        currency_value = currency_symbol_span.find_next('span', class_='currency-value').text.strip()
        return [currency_value , currency_symbol]

    # Eğer 'currency-symbol' class'ına sahip bir span yoksa, boş liste döndürülüyor
    return ["",""]


# HELPER FUNCTIONS
def get_json_script(soup, tag_type):
    json_script_tags = soup.find_all('script', {'type': 'application/ld+json'})

    # Doğru JSON script tag'ini bulmak için ek kontrol
    for script_tag in json_script_tags:
        try:
            json_data = json.loads(script_tag.string)
            # Burada özel bir kontrol yaparak doğru JSON'ı bulabilirsiniz BreadcrumbList, Product gibi
            
            if json_data.get('@type') == tag_type:
                return json_data
        except json.JSONDecodeError:
            continue  # Geçersiz JSON verisi varsa, diğer script tag'ine geç

def is_string_an_url(url_string):
    validate_url = URLValidator()
    
    try:
        validate_url(url_string)
    except ValidationError as e:
        return False

    return True

def is_string_an_integer(integer_string):
    try:
        int(integer_string)
    except ValueError:
        return False

    return True

def check_currency_in_text(text):
    currencies = Currency.objects.all()
    
    for currency in currencies:
        if currency.code in text or currency.symbol in text or currency.in_row_symbol in text:
            return True
            
    return False

def save_product_with_price():
    global product_instance
    product_instance = None
    product_instance, created = Product.objects.get_or_create(**product_data)
    price_instance = Price.objects.create(product=product_instance, **price_data)
    
    if product_instance:
        print("Product instance created")
        
    if price_instance:
        print("Price instance created")
        
    return True

# def get_proxied_response(url):
    # payload = {
    #             'api_key': '0557e7dfa1d11ce17d1dcaf1c60719be', 
    #             'url': url, 
    #             'follow_redirect': False, 
    #             'retry_404': True, 
    #             'country_code': 'us', 
    #             'device_type': 'desktop',
    #             'autoparse': True,
    #         } 

    # r = requests.get('https://api.scraperapi.com/', params=payload)

    # response = r.text