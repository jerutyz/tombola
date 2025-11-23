# tombola/quini6_scraper.py
import requests
from datetime import datetime, timedelta
import csv
import os
from bs4 import BeautifulSoup

CSV_PATH = "data/quini6.csv"
FECHAS_EXCLUIDAS_PATH = "data/quini6_fechas_excluidas.txt"

def get_last_saved_sorteo():
    """Devuelve el último sorteo guardado (el más reciente por fecha)."""
    if not os.path.exists(CSV_PATH):
        return None

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

def is_fecha_excluida(fecha):
    """Verifica si una fecha está en la lista de excluidos."""
    import os
    if not os.path.exists(FECHAS_EXCLUIDAS_PATH):
        return False
    
    fecha_str = str(fecha)
    with open(FECHAS_EXCLUIDAS_PATH, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                if line == fecha_str:
                    return True
    return False


def agregar_fecha_excluida(fecha):
    """Agrega una fecha a la lista de excluidos."""
    import os
    fecha_str = str(fecha)
    
    # Crear archivo si no existe
    if not os.path.exists(FECHAS_EXCLUIDAS_PATH):
        with open(FECHAS_EXCLUIDAS_PATH, 'w') as f:
            f.write("# Fechas sin sorteo de Quini 6\n")
            f.write("# Una fecha por línea en formato YYYY-MM-DD\n\n")
    
    # Verificar si ya está
    if is_fecha_excluida(fecha):
        return
    
    # Agregar la fecha
    with open(FECHAS_EXCLUIDAS_PATH, 'a') as f:
        f.write(f"{fecha_str}\n")


def get_last_quini6_date():
    """Devuelve el último miércoles o domingo desde hoy."""
    today = datetime.now().date()
    
    # weekday(): 0=lunes, 2=miércoles, 6=domingo
    day_of_week = today.weekday()
    
    if day_of_week == 2:  # Hoy es miércoles
        return today
    elif day_of_week == 6:  # Hoy es domingo
        return today
    elif day_of_week > 2:  # Después del miércoles
        # Último miércoles
        days_since_wednesday = day_of_week - 2
        return today - timedelta(days=days_since_wednesday)
    else:  # Antes del miércoles
        # Último domingo
        days_since_sunday = (day_of_week + 1) % 7
        return today - timedelta(days=days_since_sunday)

def next_quini6_date(date):
    """Devuelve el siguiente miércoles o domingo desde la fecha dada."""
    day_of_week = date.weekday()
    
    if day_of_week < 2:  # Lunes o martes
        # Próximo miércoles
        return date + timedelta(days=2 - day_of_week)
    elif day_of_week == 2:  # Miércoles
        # Próximo domingo (4 days)
        return date + timedelta(days=4)
    elif day_of_week < 6:  # Jueves, viernes, sábado
        # Próximo domingo
        return date + timedelta(days=6 - day_of_week)
    else:  # Domingo
        # Próximo miércoles (3 days)
        return date + timedelta(days=3)

def previous_quini6_date(date):
    """Devuelve el anterior miércoles o domingo desde la fecha dada."""
    day_of_week = date.weekday()
    
    if day_of_week <= 2:  # Lunes, martes o miércoles
        # Domingo anterior
        days_to_sunday = (day_of_week + 1) % 7
        if days_to_sunday == 0:
            days_to_sunday = 7
        return date - timedelta(days=days_to_sunday)
    else:  # Jueves en adelante
        # Miércoles anterior
        days_to_wednesday = day_of_week - 2
        return date - timedelta(days=days_to_wednesday)

def fetch_sorteo(date):
    """Busca un sorteo de Quini 6 en la fecha especificada."""
    # Determinar el día de la semana en español
    day_name = "miércoles" if date.weekday() == 2 else "domingo"
    
    url = f"https://quinieleando.com.ar/quini6/sorteo/{day_name}-{date.strftime('%d-%m-%Y')}"
    print(f"Probando: {url}")

    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if resp.status_code == 200 and "Quini 6" in resp.text:
            print("Encontrado!")
            return extract_sorteo_from_html(resp.text, date)
    except Exception as e:
        print(f"Error al buscar sorteo: {e}")
    
    return None

def extract_sorteo_from_html(html, date):
    """Extrae los números del sorteo desde el HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Extraer número de sorteo desde el <h1>
    h1 = soup.find("h1")
    if not h1:
        return None

    # El formato es: "Quini 6 Resultado<br /><small>sorteo 3323 - 19/11/2025</small>"
    # Buscar en el <small> dentro del <h1>
    small_tag = h1.find("small")
    if small_tag:
        small_text = small_tag.get_text().strip()
    else:
        small_text = h1.get_text().strip()
    
    print(f"DEBUG: Texto del header: {small_text}")
    
    sorteo_num = None
    # Buscar "sorteo XXXX"
    parts = small_text.split()
    for i, p in enumerate(parts):
        if p.lower() == "sorteo" and i + 1 < len(parts):
            try:
                sorteo_num = int(parts[i + 1])
                break
            except:
                pass

    if not sorteo_num:
        print("No se encontró número de sorteo")
        return None

    # Extraer todos los números dentro de span.numero
    numeros = []
    for span in soup.select("span.numero"):
        txt = span.get_text(strip=True)
        if txt.isdigit():
            numeros.append(int(txt))

    print(f"DEBUG: números encontrados: {numeros}")

    # Necesitamos 24 números: 6 (Tradicional) + 6 (La Segunda) + 6 (Revancha) + 6 (Siempre Sale)
    if len(numeros) < 24:
        print(f"DEBUG: números insuficientes: {len(numeros)}")
        return None

    # Los primeros 6 son Tradicional
    tradicional = numeros[0:6]
    # Los siguientes 6 son La Segunda
    la_segunda = numeros[6:12]
    # Los siguientes 6 son Revancha
    revancha = numeros[12:18]
    # Los siguientes 6 son Siempre Sale
    siempre_sale = numeros[18:24]

    result = {
        "sorteo": sorteo_num,
        "fecha": date.strftime("%Y-%m-%d"),
    }
    
    # Agregar tradicional
    for i, num in enumerate(tradicional, 1):
        result[f"t{i}"] = num
    
    # Agregar la segunda
    for i, num in enumerate(la_segunda, 1):
        result[f"s{i}"] = num
    
    # Agregar revancha
    for i, num in enumerate(revancha, 1):
        result[f"r{i}"] = num
    
    # Agregar siempre sale
    for i, num in enumerate(siempre_sale, 1):
        result[f"ss{i}"] = num

    return result

def save_to_csv(result):
    """Guarda un sorteo en el CSV ordenados por fecha."""
    os.makedirs("data", exist_ok=True)

    # Headers
    headers = ["sorteo", "fecha"] + \
              [f"t{i}" for i in range(1, 7)] + \
              [f"s{i}" for i in range(1, 7)] + \
              [f"r{i}" for i in range(1, 7)] + \
              [f"ss{i}" for i in range(1, 7)]
    
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
        **{key: str(result[key]) for key in headers[2:]}
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
