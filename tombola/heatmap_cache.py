# tombola/heatmap_cache.py
import os
from tombola.stats_cache import get_cache_date_range
from config import VISUALIZACIONES_DIR as HEATMAP_DIR



def get_heatmap_filename(juego, query_date=None):
    """Genera el nombre del archivo PNG del heatmap basado en el rango de fechas."""
    os.makedirs(HEATMAP_DIR, exist_ok=True)
    
    from_date, to_date = get_cache_date_range(juego, query_date)
    if from_date and to_date:
        return f"{HEATMAP_DIR}/{juego}_heatmap_{from_date}_to_{to_date}.png"
    else:
        return f"{HEATMAP_DIR}/{juego}_heatmap_all.png"


def load_cached_heatmap(juego, fecha_limite=None):
    """Carga heatmap desde caché si existe para el rango de fechas apropiado."""
    heatmap_file = get_heatmap_filename(juego, fecha_limite)
    
    if os.path.exists(heatmap_file):
        print(f"✅ Usando heatmap en caché: {os.path.basename(heatmap_file)}")
        return heatmap_file
    
    return None


def save_heatmap_to_cache(juego, fecha_limite, fig):
    """Guarda heatmap en caché con el nombre basado en rango de fechas."""
    heatmap_file = get_heatmap_filename(juego, fecha_limite)
    
    try:
        fig.savefig(heatmap_file, dpi=150, bbox_inches='tight')
        print(f"💾 Heatmap guardado: {os.path.basename(heatmap_file)}")
        return heatmap_file
    except Exception as e:
        print(f"⚠️  Error al guardar heatmap: {e}")
        return None


def clear_all_heatmaps():
    """Limpia todos los heatmaps en caché."""
    if not os.path.exists(HEATMAP_DIR):
        return
    
    for filename in os.listdir(HEATMAP_DIR):
        if filename.endswith('_heatmap_*.png') or filename.endswith('_heatmap_all.png'):
            try:
                os.remove(os.path.join(HEATMAP_DIR, filename))
            except:
                pass
