# tombola/stats_cache.py
import json
import os
from datetime import datetime, timedelta
from config import STATS_CACHE_DIR as CACHE_DIR



def get_next_draw_date(juego, from_date):
    """Calcula la fecha del próximo sorteo después de from_date."""
    if isinstance(from_date, str):
        from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
    
    if juego == 'telekino':
        # Telekino: sorteos solo domingos (weekday 6)
        days_until_sunday = (6 - from_date.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7  # Si ya es domingo, ir al próximo domingo
        return from_date + timedelta(days=days_until_sunday)
    
    elif juego == 'quini6':
        # Quini6: sorteos miércoles (weekday 2) y domingos (weekday 6)
        current_weekday = from_date.weekday()
        
        if current_weekday < 2:  # Lunes (0) o Martes (1)
            return from_date + timedelta(days=(2 - current_weekday))
        elif current_weekday == 2:  # Miércoles
            return from_date + timedelta(days=4)  # Próximo domingo
        elif current_weekday < 6:  # Jueves (3) a Sábado (5)
            return from_date + timedelta(days=(6 - current_weekday))
        else:  # Domingo (6)
            return from_date + timedelta(days=3)  # Próximo miércoles
    
    return None


def get_cache_date_range(juego, query_date=None):
    """
    Calcula el rango de fechas [from_date, to_date] para el cual un caché es válido.
    
    El rango va desde el día posterior al último sorteo hasta el día del próximo sorteo.
    """
    if query_date is None:
        query_date = datetime.now().date()
    elif isinstance(query_date, str):
        query_date = datetime.strptime(query_date, '%Y-%m-%d').date()
    
    if juego == 'telekino':
        # Encontrar el domingo anterior
        days_since_sunday = (query_date.weekday() + 1) % 7
        if days_since_sunday == 0:
            # Es domingo, el rango va desde hoy hasta el sábado
            from_date = query_date
            to_date = query_date + timedelta(days=6)
        else:
            # No es domingo, encontrar el último domingo
            last_sunday = query_date - timedelta(days=days_since_sunday)
            from_date = last_sunday + timedelta(days=1)  # Lunes después del sorteo
            to_date = last_sunday + timedelta(days=7)    # Domingo próximo
    
    elif juego == 'quini6':
        # Determinar el último sorteo (miércoles o domingo)
        current_weekday = query_date.weekday()
        
        if current_weekday == 0 or current_weekday == 1:  # Lunes o Martes
            # Último sorteo fue domingo
            days_since_sunday = current_weekday + 1
            last_draw = query_date - timedelta(days=days_since_sunday)
        elif current_weekday == 2:  # Miércoles (día de sorteo)
            last_draw = query_date
        elif current_weekday >= 3 and current_weekday <= 5:  # Jueves a Sábado
            # Último sorteo fue miércoles
            days_since_wednesday = current_weekday - 2
            last_draw = query_date - timedelta(days=days_since_wednesday)
        else:  # Domingo (día de sorteo)
            last_draw = query_date
        
        # El rango va desde el día después del último sorteo hasta el próximo sorteo
        from_date = last_draw + timedelta(days=1 if last_draw != query_date else 0)
        to_date = get_next_draw_date(juego, last_draw)
    
    else:
        return None, None
    
    return from_date.strftime('%Y-%m-%d'), to_date.strftime('%Y-%m-%d')


def get_cache_filename(juego, query_date=None):
    """Genera el nombre del archivo de caché basado en el rango de fechas."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    from_date, to_date = get_cache_date_range(juego, query_date)
    if from_date and to_date:
        return f"{CACHE_DIR}/{juego}_{from_date}_to_{to_date}.json"
    else:
        return f"{CACHE_DIR}/{juego}_stats_all.json"


def load_cached_stats(juego, fecha_limite=None):
    """Carga estadísticas desde caché si existe para el rango de fechas apropiado."""
    cache_file = get_cache_filename(juego, fecha_limite)
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        
        print(f"✅ Usando caché válido: {os.path.basename(cache_file)}")
        return cache_data
    except Exception as e:
        print(f"⚠️  Error al leer caché: {e}")
        return None


def save_stats_to_cache(juego, fecha_limite, stats_data):
    """Guarda estadísticas en caché con el nombre basado en rango de fechas."""
    cache_file = get_cache_filename(juego, fecha_limite)
    
    try:
        # Agregar metadata
        from_date, to_date = get_cache_date_range(juego, fecha_limite)
        
        cache_data = {
            'generated_at': datetime.now().isoformat(),
            'juego': juego,
            'valid_from': from_date,
            'valid_to': to_date,
            'stats': stats_data
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Caché guardado: {os.path.basename(cache_file)}")
        return True
    except Exception as e:
        print(f"⚠️  Error al guardar caché: {e}")
        return False


def invalidate_cache(juego):
    """Invalida todos los cachés de un juego."""
    if not os.path.exists(CACHE_DIR):
        return
    
    # Eliminar archivos de caché del juego
    for filename in os.listdir(CACHE_DIR):
        if filename.startswith(f"{juego}_"):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
            except:
                pass


def clear_all_cache():
    """Limpia todo el caché."""
    if not os.path.exists(CACHE_DIR):
        return
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
            except:
                pass
