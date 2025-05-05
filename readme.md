# Scrapping Con playwright

  Scrapping usando libreria playwright para la pagina de: **walmart.com.mx**, abre el archivo *model_file_products.xlsx* y recorre los productos listados, continua buscando cada descripcion en la pagina web inicial, se espera la lista de resultados, continua formateando dichos resultados y finalmente son exportados en los formatos: **csv, json** dentro de la carpeta "exports"
  
  ### Ambiente:
  - Ubuntu 20.04
  - python 3.11
  - playwright 1.48.0  

## 1. Tener instalado entorno virtual

    - Crear un virtual enviroment:
    $python3 -m venv venv_scrapping

    - Activarlo e instalar requirements
    $ source ./venv_scrapping/bin/activate
    (venv_scrapping)$ pip install -r requirements.txt

## 2. Correr el script
    $ python spider_wallmart.py

## Extras
    ```
    Docs:  https://playwright.dev/python/docs/intro#installing-playwright
    
    $ pip install pytest-playwright    
    # Install the required browsers:
    $ playwright install

    ```
## 4. Scrapping

  <img alt="Screenshot" src="https://raw.githubusercontent.com/wzorroman/scrapping_wallmart/refs/heads/master/screenshots/2025-05-04%2022%3A37%3A05_walmart_push-car.png" title="Sample" width="400"/>

