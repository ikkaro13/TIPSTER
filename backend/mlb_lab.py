import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

try:
    import requests
    requests.packages.urllib3.disable_warnings()
    old_merge_environment_settings = requests.Session.merge_environment_settings

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings

    requests.Session.merge_environment_settings = merge_environment_settings

    from pybaseball import standings
    from datetime import datetime
except ImportError:
    print("❌ ERROR: Necesitas instalar pybaseball primero.")
    print("👉 Ejecuta esto en tu consola: pip install pybaseball")
    exit()

def analyze_mlb_sabermetrics():
    current_year = datetime.now().year
    print(f"⚾ LABORATORIO MLB - SABERMETRÍA {current_year} ⚾")
    print("Descargando métricas desde Baseball Reference...\n")
    
    try:
        print("📊 Analizando el rendimiento de la liga...")
        # standings() devuelve una lista de DataFrames, uno por cada división (AL East, AL Cent, etc.)
        divs = standings(current_year)
        
        all_teams = []
        for df in divs:
            for index, row in df.iterrows():
                all_teams.append({
                    'Team': row['Tm'],
                    'Wins': row['W'],
                    'Losses': row['L'],
                    'Win_Pct': float(row['W-L%'])
                })
                
        # Ordenamos a los equipos por porcentaje de victorias (Win Pct)
        import pandas as pd
        league_df = pd.DataFrame(all_teams)
        top_teams = league_df.sort_values(by='Win_Pct', ascending=False).head(5)
        
        print("\n🔥 TOP 5 EQUIPOS MÁS LETALES DE LA LIGA (Win %):")
        for index, team in top_teams.iterrows():
            print(f"  {index + 1}. {team['Team']} | Win %: {team['Win_Pct']:.3f} | Récord: {team['Wins']} - {team['Losses']}")
            
        print("\n==================================================")
        print("💡 ESTRATEGIA PRE-MATCH SUGERIDA PARA HOY:")
        print("El modelo buscará partidos donde uno de estos 5 titanes enfrente")
        print("a un equipo del fondo de la tabla. Si la cuota no está demasiado castigada,")
        print("tenemos rentabilidad matemática.")
        
    except Exception as e:
        print(f"Ocurrió un error al descargar los datos: {e}")

if __name__ == "__main__":
    analyze_mlb_sabermetrics()
