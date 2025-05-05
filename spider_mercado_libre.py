import time
import re
import datetime
import random
from playwright.sync_api import sync_playwright
from process_excel import export_data, normalize_search_term, read_excel_to_list


def get_basic_random_browser_config():
    """Devuelve una configuración aleatoria de navegador"""
    browsers = [
        {'channel': 'chrome', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
        {'channel': 'chrome', 'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'},
    ]
    return random.choice(browsers)

def mercadolibre_handle_human_challenge(page, max_attempts=3):
    press_time = random.uniform(10, 15)
    
    if "blocked?url=" not in page.url.lower():
        print("No se detectó bloqueo")
        return True
    
    for attempt in range(max_attempts):
        
        page.wait_for_selector("button:has-text('Mantén presionado')", timeout=10000)
        print("Detectado Human Challenge, procediendo con la verificación...")
        
        button = page.locator("button:has-text('Mantén presionado')")
        if not button:
            print("No se pudo encontrar el botón del challenge")
            return False    
        
        try:
            print(f"Intento {attempt + 1}: Manteniendo presionado por {press_time:.1f}s")
            button.click(delay=press_time*1000)
            
            # Esperar a que desaparezca el challenge
            try:
                button.wait_for(state="hidden", timeout=5000)
                page.wait_for_load_state("networkidle", timeout=10000)
                return True
            except:
                if attempt == max_attempts - 1:
                    print("Máximo de intentos alcanzado")
                    return False
                continue    
                
        except:
            print("No se detectó Human Challenge, continuando...")
            return False
    
def normalize_all_term(search_term: str) -> str:
    words = search_term.split()
    normalized_term = '-'.join(words).lower()    
    return normalized_term

def extract_mercadolibre_product_data(search_term, browser_config):
    with sync_playwright() as p:
        # start the browser
        browser = p.chromium.launch(
                channel=browser_config['channel'],
                headless=False
            )            
        context = browser.new_context(user_agent=browser_config['user_agent'])
        
        # load the page
        page = context.new_page()
        website_base = "https://listado.mercadolibre.com.mx"
        
        search_term_sanitize = normalize_all_term(search_term)
        page.goto(f"{website_base}/{search_term_sanitize}")        
        print("Esperando a que se cargue el contenido...")
        wait_time_load = random.uniform(5, 10)
        time.sleep(wait_time_load)        
        
        name_img = normalize_search_term(search_term)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page.screenshot(path=f"screenshots/{current_time}_mercadoLibre_{name_img}.png")
        print(" screenshoot...")
        
        products_data = []
        
        # find the product items
        product_items = page.query_selector_all('ol.ui-search-layout--grid li.ui-search-layout__item')
        
        for item in product_items:
            product = {}
            
            # Extract title
            title_element = item.query_selector('.poly-component__title')
            if title_element:
                product['title'] = title_element.inner_text().strip()
            
            # Extract seller
            seller_element = item.query_selector('.poly-component__seller')
            if seller_element:
                product['seller'] = seller_element.inner_text().replace('Por ', '').strip()
                # Check if it's an official store
                product['official_store'] = bool(seller_element.query_selector('svg[aria-label="Tienda oficial"]'))
            
            # Extract price information
            current_price_element = item.query_selector('.poly-price__current .andes-money-amount__fraction')
            if current_price_element:
                product['current_price'] = current_price_element.inner_text().strip()
            
            previous_price_element = item.query_selector('.andes-money-amount--previous .andes-money-amount__fraction')
            if previous_price_element:
                product['previous_price'] = previous_price_element.inner_text().strip()
            
            discount_element = item.query_selector('.andes-money-amount__discount')
            if discount_element:
                product['discount'] = discount_element.inner_text().strip()
            
            # Extract installments
            installments_element = item.query_selector('.poly-price__installments')
            if installments_element:
                product['installments'] = installments_element.inner_text().strip()
            
            # Extract shipping info
            shipping_element = item.query_selector('.poly-component__shipping')
            if shipping_element:
                product['shipping'] = shipping_element.inner_text().strip()
            
            # Extract rating
            rating_element = item.query_selector('.poly-reviews__rating')
            if rating_element:
                product['rating'] = rating_element.inner_text().strip()
            
            rating_count_element = item.query_selector('.poly-reviews__total')
            if rating_count_element:
                product['rating_count'] = rating_count_element.inner_text().strip('()')
            
            # Extract the main product image from carousel
            carousel_wrapper = item.query_selector('.andes-carousel-snapped__wrapper')
            if carousel_wrapper:
                # Get the first active image in the carousel
                main_image = carousel_wrapper.query_selector('.andes-carousel-snapped__slide--active img.poly-component__picture')
                if main_image:
                    product['main_image'] = main_image.get_attribute('src')
                    product['main_image_alt'] = main_image.get_attribute('alt')
            
            # Extract the product detail link (there are multiple possible locations)
            # Option 1: From the title link
            title_link = item.query_selector('.poly-component__title-wrapper a')
            if title_link:
                product['detail_url'] = title_link.get_attribute('href')
            else:
                # Option 2: From the carousel image link (fallback)
                carousel_link = item.query_selector('.andes-carousel-snapped__slide--active a.poly-component__link--carousel')
                if carousel_link:
                    product['detail_url'] = carousel_link.get_attribute('href')
            
            # Extract color variations if available
            color_variations = item.query_selector_all('.poly-variations__item')
            if color_variations:
                product['color_variations'] = []
                for color in color_variations:
                    color_img = color.query_selector('img')
                    if color_img:
                        product['color_variations'].append({
                            'color': color_img.get_attribute('title'),
                            'image_url': color_img.get_attribute('src')
                        })
            
            products_data.append(product)
        
        
        browser.close()
        
        return products_data


def process():
    file_path = "model_file_products.xlsx"
    data_list = read_excel_to_list(file_path)

    for item in data_list:
        search_term = item['Producto']
        print(f"\n" + "="*30)
        print(f"Extrayendo datos para: '{search_term}'...")
        browser_config = get_basic_random_browser_config()
        products = extract_mercadolibre_product_data(search_term, browser_config)        
        export_data(products, search_term, page_origin="mercadolibre")
        
        # Esperar un tiempo aleatorio entre búsquedas
        time_between_searches = random.uniform(3, 7)
        print(f"Esperando {time_between_searches:.2f}s para próxima búsqueda...")
        time.sleep(time_between_searches)
    
    print(f"\n" + "="*20)
    print("Proceso de extracción de datos finalizado.")

def process2():
    # search_term = "pilas recargables usb"
    search_term = "Push Car Prinsel Adventure Rojo"
    # search_term = "playhouse 2 en 1 prinsel unisex"
    
    browser_config = get_basic_random_browser_config()
    products = extract_mercadolibre_product_data(search_term, browser_config) 
    export_data(products, search_term, page_origin="mercadolibre")
        
if __name__ == "__main__":
    process()
