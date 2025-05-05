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

def wallmart_handle_human_challenge(page, max_attempts=3):
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
    

def extract_product_data(search_term, browser_config):
    with sync_playwright() as p:
        # Iniciar el navegador
        browser = p.chromium.launch(
                channel=browser_config['channel'],
                headless=False
            )            
        context = browser.new_context(user_agent=browser_config['user_agent'])
        
        # Navegar a la página de búsqueda
        page = context.new_page()
        website_base = "https://www.walmart.com.mx"
        
        search_term_sanitize = search_term.strip().lower().replace(' ', '+')
        page.goto(f"{website_base}/search?q={search_term_sanitize}")        
        print("Esperando a que se cargue el contenido...")
        wait_time_load = random.uniform(5, 10)
        time.sleep(wait_time_load)
        
        wallmart_handle_human_challenge(page)
        
        name_img = normalize_search_term(search_term)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page.screenshot(path=f"screenshots/{current_time}_walmart_{name_img}.png")
        print(" screenshoot...")
        
        # Esperar a que el contenido se cargue
        page.wait_for_selector('[data-testid="item-stack"]')
        
        # Localizar el div principal
        item_stack = page.query_selector('[data-testid="item-stack"]')
        
        # Lista para almacenar los datos de los productos
        products_data = []
        
        # Buscar todos los divs con role="group" y data-item-id dentro del item-stack
        product_groups = item_stack.query_selector_all('div[role="group"][data-item-id]')
        total_products = len(product_groups)
        print(f"Se encontraron {total_products} productos.")
        i = 0
        
        for group in product_groups:
            print("Extrayendo datos del producto...")
            product_data = {}
            
            # Extraer el título del producto
            title_span = group.query_selector('span[data-automation-id="product-title"]')
            if title_span:
                product_data['title'] = title_span.inner_text().strip()
            
            # Extraer el enlace del producto
            product_link = group.query_selector('a.w-100.h-100.z-1.hide-sibling-opacity.absolute[href]')
            if product_link:
                href = product_link.get_attribute('href')
                product_data['link'] = f"{website_base}{href}" if href.startswith('/') else href
                
            # Extraer información de precios
            price_div = group.query_selector('div[data-automation-id="product-price"]')
            if price_div:
                price_spans = price_div.query_selector_all('span.w_q67L')
                price_info = [span.inner_text().strip() for span in price_spans if span.inner_text().strip()]
                
                # Procesar la información de precios para extraer valores específicos
                current_price = None
                old_price = None                
                
                for info in price_info:
                    if 'precio actual' in info.lower():
                        current_price = info
                        # convertir el precio a float
                        price_match = re.search(r'\$\s*([\d,]+\.\d{2})', info)
                        if price_match:
                            current_price_float = float(price_match.group(1).replace(',', ''))
                            
                    elif 'costaba' in info.lower():
                        old_price = info
                    
                product_data['current_price'] = current_price
                product_data['price'] = current_price_float
                product_data['old_price'] = old_price
                product_data['full_price_info'] = " | ".join(price_info)
            
            # Extraer la marca del producto
            brand_div = group.query_selector('div.mb1.mt2.b.f6.black.mr1.lh-copy')
            if brand_div:
                product_data['brand'] = brand_div.inner_text().strip()
            
            # Extraer la imagen del producto
            img_div = group.query_selector('div.relative.overflow-hidden img')
            if img_div:
                product_data['photo'] = img_div.get_attribute('src')
            
            i += 1
            print(f"\nProducto {i}:")
            print(f" Título       : {product_data.get('title', '-')}")
            print(f" Marca        : {product_data.get('brand', '-')}")
            print(f" Precio actual: {product_data.get('price', '-')}")
            print(f" Precio ant   : {product_data.get('old_price', '-')}")            
            print(f" price_info   : {product_data.get('full_price_info', '-')}")
            #print(f" photo: {product_data.get('photo', '-')}")
            #print(f" link: {product_data.get('link', '-')}")
            print("-"*20)
            
            # Solo agregar el producto si tenemos al menos el título
            if 'title' in product_data:
                products_data.append(product_data)
        
        
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
        products = extract_product_data(search_term, browser_config)        
        export_data(products, search_term)
        
        # Esperar un tiempo aleatorio entre búsquedas
        time_between_searches = random.uniform(3, 7)
        print(f"Esperando {time_between_searches:.2f}s para próxima búsqueda...")
        time.sleep(time_between_searches)
    
    print(f"\n" + "="*20)
    print("Proceso de extracción de datos finalizado.")


if __name__ == "__main__":
    process()
