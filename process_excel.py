import datetime
import pandas as pd
from pathlib import Path
import pandas as pd
import json
from typing import List

def read_excel_to_list(file_path) -> list:
    # Leer el archivo Excel - Campos:
    #  'SkuProducto': 1630, 
    #  'Producto': 'Push Car Prinsel Adventure Rojo', 
    #  'Linea': 'Prinsel', 
    #  'Grupo': 'Juguetes', 
    #  'Categoria': 'Juguetes', 
    #  'SubCategoria': 'Juguetes', 
    #  'SubSubCatego': 'Juguetes', 
    #  'Area': 'Juguetes', 
    #  'Estado': 'VIGENTE'
    
    data = pd.read_excel(file_path)
    data_list = data.to_dict(orient='records')    
    return data_list

def normalize_search_term(search_term: str) -> str:
    words = search_term.split()
    filtered_terms = words[:2]
    normalized_term = '-'.join(filtered_terms).lower()    
    return normalized_term

def export_data(products_data: List, search_term: str)-> tuple:
    # Crear directorio de exportación si no existe
    export_dir = Path('exports')
    export_dir.mkdir(exist_ok=True)
    
    nterm = normalize_search_term(search_term)    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_base = f"{timestamp}_walmart_search_{nterm}"
    
    # Exportar a CSV
    df = pd.DataFrame(products_data)
    csv_path = export_dir / f"{filename_base}.csv"
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    
    # Exportar a JSON
    json_path = export_dir / f"{filename_base}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(products_data, f, ensure_ascii=False, indent=2)
    
    print(f"\nDatos exportados exitosamente:")
    print(f"- CSV : {csv_path}")
    print(f"- JSON: {json_path}")
    
    return csv_path, json_path


# if __name__ == "__main__":
#     file_path = "model_file_products.xlsx"
#     data_list = read_excel_to_list(file_path)
#     # print(data_list)
    
#     for item in data_list:
#         print("\n" + "=" * 40)
#         print(f"Producto| SKU:{item['SkuProducto']} - ({item['Estado']})")
#         print(f"Línea: {item['Linea']}, Categoria: {item['Categoria']}")
#         print(f"{item['Producto']}")
#         print("-" * 40)
    
      
    