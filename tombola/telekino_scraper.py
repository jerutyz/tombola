# src/scrape_telekino.py
import requests
from datetime import datetime, timedelta
import csv
import os
from bs4 import BeautifulSoup
from pathlib import Path

CSV_PATH = "data/telekino.csv"

def get_last_saved_sorteo():
    """Devuelve el último sorteo guardado (el más reciente por fecha)."""
    if not os.path.exists(CSV_PATH):
        return None  # No hay archivo todavía

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return None

    # Encontrar el sorteo con la fecha más reciente
    newest = None
    newest_date = None
    
    for row in rows:
        try:
            fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
            if newest_date is None or fecha > newest_date:
                newest_date = fecha
                newest = row
        except:
            continue

    if not newest:
        return None

    return {
        "sorteo": int(newest["sorteo"]),
        "fecha": newest_date
    }

def get_first_saved_sorteo():
    """Devuelve el primer sorteo guardado (el más antiguo por fecha)."""
    if not os.path.exists(CSV_PATH):
        return None

    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return None

    # Encontrar el sorteo con la fecha más antigua
    oldest = None
    oldest_date = None
    
    for row in rows:
        try:
            fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
            if oldest_date is None or fecha < oldest_date:
                oldest_date = fecha
                oldest = row
        except:
            continue

    if not oldest:
        return None

    return {
        "sorteo": int(oldest["sorteo"]),
        "fecha": oldest_date
    }

def previous_telekino_date(date):
    return date - timedelta(days=7)

def next_telekino_date(date):
    """Devuelve el siguiente domingo desde la fecha dada."""
    return date + timedelta(days=7)

def get_all_saved_sorteos():
    """Devuelve un set con todas las fechas de sorteos guardados."""
    if not os.path.exists(CSV_PATH):
        return set()
    
    saved_dates = set()
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
                saved_dates.add(fecha)
            except:
                pass
    
    return saved_dates

def get_last_sunday():
    """Devuelve el último domingo desde hoy."""
    today = datetime.now().date()
    days_since_sunday = (today.weekday() + 1) % 7
    last_sunday = today - timedelta(days=days_since_sunday)
    return last_sunday

def fetch_sorteo_old(date):
    url = f"https://quinieleando.com.ar/telekino/sorteo/domingo-{date.strftime('%d-%m-%Y')}"
    print("buscar sorteo ")
    print(url)
    resp = requests.get(url)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # Título con número de sorteo
    h1 = soup.find("h1")
    if not h1:
        return None
    header_text = h1.get_text().strip()  # ej: "Telekino Resultado Sorteo 2401 domingo, 9 de noviembre de 2025"
    parts = header_text.split()
    sorteo_num = None
    for i, p in enumerate(parts):
        if p.lower() == "sorteo" and i+1 < len(parts):
            try:
                sorteo_num = int(parts[i+1])
            except:
                pass

    # Extraer los números de Telekino
    # Están probablemente en el texto justo después del h1, separados con espacios
    # Vamos a buscar tags <h1> y luego los siguientes hermanos de texto
    telekino_numbers = []
    # Buscamos todo el texto en el contenido, y luego un patrón
    body_text = soup.get_text(separator="\n")
    lines = body_text.split("\n")
    # filtrar líneas que tienen solo números separados por espacios
    for line in lines:
        tokens = line.strip().split()
        if len(tokens) >= 3 and all(tok.isdigit() for tok in tokens):
            # puede ser parte de los 15 números o ReKino, hay que decidir
            # por cómo está en la página: los primeros 5 lines son Telekino
            telekino_numbers.extend([int(tok) for tok in tokens])

    # Asumimos que los 15 primeros enteros que encontramos son Telekino
    telekino_numbers = telekino_numbers[:15]

    if len(telekino_numbers) != 15:
        # Si no encontramos exactamente 15, consideramos que falló
        return None

    return {
        "sorteo": sorteo_num,
        "fecha": date.strftime("%Y-%m-%d"),
        **{f"n{i+1}": telekino_numbers[i] for i in range(15)}
    }

def fetch_sorteo(date):
    base = "https://quinieleando.com.ar/telekino/sorteo"

    url = f"{base}/domingo-{date.strftime('%d-%m-%Y')}"
    print("Probando:", url)

    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code == 200 and "Telekino" in resp.text:
        print("Encontrado!")
        #print(resp.text)
        return extract_sorteo_from_html(resp.text, date)

    return None


def fetch_last_sorteo():
    base = "https://quinieleando.com.ar/telekino/sorteo"
    today = datetime.date.today()

    for i in range(60):  # revisamos 60 domingos atrás
        date = today - datetime.timedelta(days=i)
        
        # Solo domingos
        if date.weekday() != 6:
            continue

        # Si es hoy, lo saltamos (la página nunca tiene ese sorteo cargado todavía)
        if date == today:
            print(f"Saltando {date} porque coincide con hoy...")
            continue

        url = f"{base}/domingo-{date.strftime('%d-%m-%Y')}"
        print("Probando:", url)

        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code == 200 and "Telekino" in resp.text:
            print("Encontrado!")
            #print(resp.text)
            return extract_sorteo_from_html(resp.text, date)

    return None

def extract_sorteo_from_html(html, date):
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Extraer número de sorteo desde el <h1>
    h1 = soup.find("h1")
    if not h1:
        return None

    header_text = h1.get_text().strip().split()
    sorteo_num = None
    for i, p in enumerate(header_text):
        if p.lower() == "sorteo" and i + 1 < len(header_text):
            try:
                sorteo_num = int(header_text[i + 1])
            except:
                pass

    # Extraer todos los números dentro de span.numero
    telekino_numbers = []
    for span in soup.select("span.numero"):
        txt = span.get_text(strip=True)
        if txt.isdigit():
            telekino_numbers.append(int(txt))

    print("DEBUG: números encontrados:", telekino_numbers)

    # → Quedarnos solo con los primeros 15 (Telekino)
    telekino_numbers = telekino_numbers[:15]

    if len(telekino_numbers) < 15:
        print("DEBUG: números insuficientes:", telekino_numbers)
        return None

    return {
        "sorteo": sorteo_num,
        "fecha": date.strftime("%Y-%m-%d"),
        **{f"n{i+1}": telekino_numbers[i] for i in range(15)}
    }


def save_to_csv(result):
    # Crea carpeta data si no existe
    os.makedirs("data", exist_ok=True)

    # Headers
    headers = ["sorteo", "fecha"] + [f"n{i}" for i in range(1,16)]
    
    # Leer todos los sorteos existentes
    sorteos = []
    if os.path.isfile(CSV_PATH):
        with open(CSV_PATH, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            sorteos = list(reader)
    
    # Verificar si el sorteo ya existe
    for sorteo in sorteos:
        if str(sorteo["sorteo"]) == str(result["sorteo"]):
            print(f"⚠️ El sorteo {result['sorteo']} ya está guardado. No se duplica.")
            return False
    
    # Agregar el nuevo sorteo
    sorteos.append({
        "sorteo": str(result["sorteo"]),
        "fecha": result["fecha"],
        **{f"n{i}": str(result[f"n{i}"]) for i in range(1, 16)}
    })
    
    # Ordenar por fecha (del más viejo al más nuevo)
    sorteos.sort(key=lambda x: datetime.strptime(x["fecha"], "%Y-%m-%d").date())
    
    # Reescribir todo el CSV ordenado
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sorteos)
    
    print(f"✔️ Sorteo {result['sorteo']} guardado en {CSV_PATH}")
    return True


# Ejemplo de prueba
if __name__ == "__main__":
    d = datetime.strptime("2025-11-09", "%Y-%m-%d")
    rec = fetch_sorteo(d)
    print(rec)
