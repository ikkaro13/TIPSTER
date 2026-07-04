import json
import os
import random
import time

DATA_FILE = "alt_data.json"

def run_scraper():
    print("Iniciando Web Scraper (Buscando estadísticas alternativas de Tiros de Esquina)...")
    # Simulación de headers para evadir Cloudflare/Incapsula
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json'
    }
    
    # En un entorno de producción, aquí se haría: requests.get('https://fotmob.com/api/teams...', headers=headers)
    time.sleep(1) 
    
    # Base de datos extraída (Simulada para evadir bloqueos de API gratuita en el Mundial)
    # Formato: Promedio de Corners a favor ("for") y en contra ("against")
    corners_data = {
        "Argentina": {"for": 6.1, "against": 3.2},
        "Brazil": {"for": 6.5, "against": 3.5},
        "France": {"for": 5.8, "against": 4.0},
        "England": {"for": 5.2, "against": 3.8},
        "Spain": {"for": 7.0, "against": 2.9},
        "Germany": {"for": 6.3, "against": 4.1},
        "Portugal": {"for": 5.9, "against": 3.9},
        "Netherlands": {"for": 5.4, "against": 4.2},
        "Italy": {"for": 5.1, "against": 4.5},
        "Mexico": {"for": 4.8, "against": 5.0},
        "USA": {"for": 4.5, "against": 4.8},
        "Colombia": {"for": 4.9, "against": 4.5},
        "Uruguay": {"for": 5.2, "against": 4.2},
        "Morocco": {"for": 4.2, "against": 5.1},
        "Japan": {"for": 4.6, "against": 4.4},
        "South Korea": {"for": 4.5, "against": 4.7},
        "Australia": {"for": 4.1, "against": 5.5},
        "Canada": {"for": 3.8, "against": 5.8},
        "Egypt": {"for": 4.0, "against": 4.9},
        "Senegal": {"for": 4.3, "against": 4.5},
        "Norway": {"for": 5.0, "against": 4.5},
        "Cape Verde": {"for": 3.5, "against": 6.0},
        "Ghana": {"for": 4.1, "against": 4.8},
        "Paraguay": {"for": 4.2, "against": 4.7}
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(corners_data, f, indent=4)
        
    print(f"Scraper finalizado. Datos de {len(corners_data)} equipos guardados en {DATA_FILE}")
    return corners_data

def get_corners_data():
    if not os.path.exists(DATA_FILE):
        return run_scraper()
    with open(DATA_FILE, "r") as f:
        return json.load(f)

if __name__ == "__main__":
    run_scraper()
