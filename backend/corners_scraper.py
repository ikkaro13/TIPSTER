import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import pandas as pd
import io
import json
import os
import time

CORNERS_DB_FILE = os.path.join(os.path.dirname(__file__), "corners_db.json")

def scrape_soccerstats_corners(league_str):
    print(f"[GhostScraper] Infiltrandose en SoccerStats usando Chrome Invisible para la liga: {league_str}...")
    url = f"https://www.soccerstats.com/corners.asp?league={league_str}"
    
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    
    # Try to initialize the browser
    try:
        driver = uc.Chrome(options=options)
    except Exception as e:
        print(f"Error initializing Chrome: {e}")
        return None
        
    try:
        driver.get(url)
        time.sleep(3) # Wait for Cloudflare
        
        html = driver.page_source
        tables = pd.read_html(io.StringIO(html))
        
        corners_data = {}
        for df in tables:
            if len(df.columns) >= 4 and len(df) > 5:
                text_dump = " ".join(df.astype(str).values.flatten()).lower()
                if "total" in text_dump and "home" in text_dump and "away" in text_dump:
                    print("[GhostScraper] Tabla candidata encontrada!")
                    
                    header_row_idx = None
                    for idx, row in df.iterrows():
                        row_text = " ".join(str(x).lower() for x in row.values)
                        if "team" in row_text or "total" in row_text:
                            header_row_idx = idx
                            break
                    
                    if header_row_idx is not None:
                        df.columns = df.iloc[header_row_idx]
                        df = df.iloc[header_row_idx+1:].reset_index(drop=True)
                        
                        for idx, row in df.iterrows():
                            team_name = str(row.iloc[0]).strip()
                            if team_name and team_name.lower() != "nan" and team_name.lower() != "team":
                                try:
                                    total_c = str(row.iloc[2]).strip()
                                    home_c = str(row.iloc[3]).strip()
                                    away_c = str(row.iloc[4]).strip()
                                    
                                    corners_data[team_name] = {
                                        "total_corners_avg": total_c,
                                        "home_corners_avg": home_c,
                                        "away_corners_avg": away_c
                                    }
                                except Exception as inner_e:
                                    pass
                        
                        break
        
        return corners_data
        
    except Exception as e:
        print(f"[GhostScraper] Error de extraccion: {e}")
        return None
    finally:
        driver.quit()

def update_corners_db(league_str):
    data = scrape_soccerstats_corners(league_str)
    if data:
        db = {}
        if os.path.exists(CORNERS_DB_FILE):
            with open(CORNERS_DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)
                
        db[league_str] = data
        
        with open(CORNERS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4, ensure_ascii=False)
        print(f"[GhostScraper] Guardados {len(data)} equipos de {league_str} en corners_db.json")
        # Print a sample
        print("Muestra de datos:")
        for k, v in list(data.items())[:3]:
            print(f" - {k}: {v}")
    else:
        print("[GhostScraper] No se pudo encontrar datos validos de corners.")

if __name__ == "__main__":
    update_corners_db("england")
