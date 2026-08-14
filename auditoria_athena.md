# AUDITORÍA DE SISTEMA: ATHENA ENGINE

## A. Informe de Auditoría ATHENA

**Estado General:** El proyecto ha transitado exitosamente desde un esqueleto en papel hasta una aplicación monolítica funcional. La integración entre el frontend (React/Next.js) y el backend (FastAPI/Python) es sólida. Se ha implementado exitosamente la extracción de datos (Scraping de SofaScore y API-Football), el motor predictivo (Hermes/Athena) que utiliza Poisson y Machine Learning (Random Forest) para predecir probabilidades y detectar *Value Bets*, un gestor de portafolio simulado (Plutus) para el *paper trading*, un sistema de alertas por Telegram y una estética de grado profesional.

### Análisis de Módulos (Clasificación)
🟢 **Implementado y funcional**
🟡 **Implementado pero requiere validación (Fase de Campo)**
🟠 **Parcial (Mockeado o incompleto)**
🔴 **Falta**
⚪ **Planeado (Futuro)**

- 🟢 **Estructura Base:** Frontend (Next.js) y Backend (FastAPI).
- 🟢 **Extracción PRE-PARTIDO:** API-Football (Fixtures, equipos).
- 🟢 **Extracción EN VIVO:** SofaScore Scraper (Estadísticas en tiempo real, Momentum, GPI).
- 🟢 **Extracción de Cuotas (Odds):** Integrado a través de `odds_connector.py`.
- 🟢 **Motor Hermes (Lógica Core):** Análisis de Poisson y Random Forest.
- 🟢 **Cálculo de Probabilidad, Confianza, EV:** Generado por `hermes.py` y `athena_engine.py`.
- 🟢 **Selección de Mercado:** Actualmente centrado en Match Winner (1X2) y Over 0.5 HT en Vivo.
- 🟢 **Lógica NO BET:** Implementada (Filtros de Edge < 5% o Cuotas < 1.60).
- 🟢 **Sistema de Gestión de Capital (Plutus):** Bankroll visual y Tracker de Apuestas en `portfolio_db.json`.
- 🟢 **Alertas Externas:** Integración funcional con Telegram (`telegram_bot.py`).
- 🟢 **Interfaz Gráfica (Dashboard):** Tema Cyberpunk completado con Data-Grids y Glassmorphism.
- 🟡 **Motor de Autopsia / Aprendizaje:** `autopsy_engine.py` implementado para evaluar picks, pero requiere validación alimentándolo con datos reales.
- 🟡 **Cálculo de AVI (Algorithmic Value Index):** Implementado lógicamente, pero los umbrales necesitan calibración de campo.
- 🟠 **Recomendación de Stake:** El stake está parcialmente fijo o calculado de manera básica, sin Criterio de Kelly avanzado dinámico.
- 🔴 **Protección estricta de Timestamps:** Aún no hay un pipeline complejo para evitar cruce de datos en backtesting masivo (aunque no afecta el *forward-testing* actual).
- ⚪ **Despliegue en la Nube (Producción):** Actualmente alojado en `localhost`.

---

## B. Árbol Estructural del Proyecto Actual

```text
TIPSTER/
├── INICIAR_TIPSTER.bat
├── zip_project.py
├── backend/
│   ├── .env
│   ├── main.py (Punto de entrada de FastAPI y rutas)
│   ├── api_football_engine.py (Conexión API Externa)
│   ├── sofascore_scraper.py (Extracción Live)
│   ├── odds_connector.py (Extracción de Cuotas)
│   ├── telegram_bot.py (Alertas al celular)
│   ├── portfolio_manager.py (Lógica Plutus)
│   ├── autopsy_engine.py (Motor de revisión post-partido)
│   ├── calibrate_brain.py (Recalibración del modelo)
│   ├── athena_engine.py (Reglas LIVE y GPI)
│   ├── tipster.db / portfolio_db.json (Almacenamiento)
│   ├── decision_corpus.jsonl (Registro de aprendizaje)
│   ├── model.pkl / scaler.joblib (Modelos ML pre-entrenados)
│   ├── requirements.txt
│   └── engine/
│       ├── hermes.py (Matemática pura y Poisson)
│       └── rules.py (Reglas de filtrado)
└── frontend/
    ├── package.json
    ├── next.config.ts
    └── src/app/
        ├── globals.css (Design System Cyberpunk)
        ├── layout.tsx
        └── page.tsx (Dashboard Monolítico)
```

---

## C. ROADMAP vs Implementación Actual

| Fase del Roadmap | Estado | Comentarios |
| :--- | :---: | :--- |
| **Fase 1: Setup e Infraestructura** | 🟢 100% | FastAPI + Next.js corriendo simultáneamente. |
| **Fase 2: Interfaz Visual Básica** | 🟢 100% | Sustituida por la versión Premium Cyberpunk (Fase 5). |
| **Fase 3: Data Engine (API-Football)** | 🟢 100% | Conexión lograda. Extrae cartelera, stats y cuotas. |
| **Fase 4: Modelo Hermes (Predictivo)** | 🟢 100% | Algoritmo Poisson + Random Forest generando predicciones y determinando Edge. |
| **Fase 5: Plutus y Chronos (UI Avanzada)** | 🟢 100% | Data-Grids interactivos, Bankroll visual dinámico y alertas Live. |
| **Fase 6: Autopsia y Auto-aprendizaje** | 🟡 90% | Backend implementado (`autopsy_engine.py`), falta probar iterativamente con +100 resultados reales. |

---

## D. Archivos Principales y su Función

- `backend/main.py`: El corazón del sistema. Enruta las peticiones de la interfaz web hacia los scripts lógicos de Python (Ej. llamar a Hermes o enviar alertas por Telegram).
- `backend/engine/hermes.py`: El cerebro matemático. Calcula la probabilidad de goles, el Expected Value (EV) y define si vale la pena apostar (Edge > 5%).
- `backend/athena_engine.py`: Motor de lógica EN VIVO. Calcula el Momentum y el *Goal Pressure Index (GPI)*.
- `backend/autopsy_engine.py`: El maestro evaluador. Lee los resultados de partidos pasados y juzga si Hermes se equivocó o acertó.
- `backend/sofascore_scraper.py`: Extrae estadísticas invisibles o de alto costo (ataques peligrosos en vivo) evadiendo pagos de APIs costosas.
- `frontend/src/app/page.tsx`: La cara gráfica del proyecto (Dashboard). Muestra Chronos (Calendario), Argos (Radar Live) y Plutus (Billetera).
- `frontend/src/app/globals.css`: Define toda la estética premium de la interfaz (colores neón, fondos oscuros, glassmorphism).

---

## E. Dependencias Externas Utilizadas

**Backend (Python):**
- `fastapi` & `uvicorn` (Servidor web asíncrono y enrutador).
- `scikit-learn` (Algoritmos de Machine Learning).
- `pandas` & `numpy` & `scipy` (Análisis de datos, matrices y distribuciones estadísticas Poisson).
- `requests` (Peticiones HTTP a API-Football, Telegram y Scraper).

**Frontend (Node.js):**
- `next` & `react` (Framework web y motor UI).
- CSS puro (Vanilla) para estilización sin dependencias extra como Tailwind.

---

## F. Comandos Necesarios para Ejecutar el Sistema

Para iniciar el sistema localmente desde cero:

1. **Terminal 1 (Backend):**
   ```bash
   cd D:\Work\ANTIGRAVITY\TIPSTER\backend
   uvicorn main:app --reload
   ```

2. **Terminal 2 (Frontend):**
   ```bash
   cd D:\Work\ANTIGRAVITY\TIPSTER\frontend
   npm run dev
   ```

*(Nota: Tienes un archivo `INICIAR_TIPSTER.bat` en la raíz que probablemente hace esto de forma automática con doble clic).*

---

## G. Problemas, Errores Conocidos y Riesgos Técnicos

> [!WARNING]
> 1. **Límites de API-Football:** Si usas la versión gratuita (100 peticiones), ATHENA fallará o devolverá arrays vacíos si dejas el escáner Live mucho tiempo abierto.
> 2. **Fragilidad del Scraper (SofaScore):** `sofascore_scraper.py` depende de la estructura HTML/JSON interna de una web de terceros. Si SofaScore cambia sus IDs o estructura de URLs, el motor en vivo se romperá y requerirá mantenimiento de código.
> 3. **Gestión de Sesión:** Actualmente Plutus (`portfolio_db.json`) maneja los datos en un JSON plano local. Si varios usuarios operan o si ocurre un fallo eléctrico durante la escritura, el JSON podría corromperse.
> 4. **Mocking Restante:** Si API-Football no tiene cuotas pre-match en ligas muy oscuras, el sistema asigna cuotas simuladas (`mock`).

---

## H. Recomendación de Siguiente Paso

**NO RECOMIENDO AGREGAR CÓDIGO NUEVO POR EL MOMENTO.**

El sistema ha alcanzado el punto de *Features Complete* respecto al plan inicial. El siguiente paso lógico, obligatorio e inamovible es la **Fase de Campo (Forward Testing)**:

Debes usar a ATHENA tal como está, durante 7 a 14 días. Simula 100 apuestas (50 pre-partido, 50 en vivo). Ejecuta la Autopsia diariamente y observa el porcentaje de *Win Rate* y *ROI* en la pestaña Plutus. Solo cuando el archivo `decision_corpus.jsonl` tenga al menos 100 operaciones evaluadas por la autopsia, sabremos matemáticamente qué parte del código predictivo requiere un ajuste (refactorización) y qué parte es perfecta.
