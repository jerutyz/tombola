import csv
from collections import Counter, defaultdict
from itertools import combinations
import random
from .base_game import BaseGame
from config import DATA_DIR

CSV_PATH = f"{DATA_DIR}/telekino.csv"



class Telekino(BaseGame):
    def draw(self):
        """Devuelve un sorteo aleatorio de 15 números entre 1 y 25."""
        return sorted(random.sample(range(1, 26), 15))

    def num_range(self):
        """Devuelve el rango total de números válidos del juego."""
        return range(1, 26)

    def picks(self):
        """Devuelve cuántos números se sortean."""
        return 15



def load_data(fecha_limite=None):
    """
    Devuelve:
    - lista de sorteos (dicts)
    - lista de números por cada sorteo
    
    Si fecha_limite está definida (formato YYYY-MM-DD o date object),
    solo carga sorteos anteriores a esa fecha (útil para backtesting).
    """
    from datetime import datetime
    
    sorteos = []
    numeros_por_sorteo = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filtrar por fecha si se especifica
            if fecha_limite:
                fecha_sorteo = datetime.strptime(row['fecha'], '%Y-%m-%d').date()
                if isinstance(fecha_limite, str):
                    fecha_limite = datetime.strptime(fecha_limite, '%Y-%m-%d').date()
                if fecha_sorteo >= fecha_limite:
                    continue  # Saltar sorteos >= fecha_limite
            
            sorteos.append(row)
            nums = [int(row[f"n{i}"]) for i in range(1, 16)]
            numeros_por_sorteo.append(nums)

    return sorteos, numeros_por_sorteo


def calcular_frecuencias(numeros_por_sorteo):
    counter = Counter()
    for nums in numeros_por_sorteo:
        counter.update(nums)
    return counter


def calcular_omision(sorteos, numeros_por_sorteo):
    """
    Omisión = hace cuántos sorteos no apareció cada número del 1 al 25.
    Cuenta desde el sorteo más reciente hacia atrás.
    """
    ultimas_apariciones = {n: None for n in range(1, 26)}

    # Recorrer desde el sorteo MÁS RECIENTE (último en la lista) hacia el más antiguo
    # Invertir la lista para que idx=0 sea el más reciente
    for idx, nums in enumerate(reversed(numeros_por_sorteo)):
        for n in nums:
            if ultimas_apariciones[n] is None:
                ultimas_apariciones[n] = idx  # distancia desde el último sorteo

    # Reemplazar None por "nunca apareció"
    for n in ultimas_apariciones:
        if ultimas_apariciones[n] is None:
            ultimas_apariciones[n] = len(numeros_por_sorteo)

    return ultimas_apariciones


def calcular_demora_maxima(sorteos, numeros_por_sorteo):
    """
    Calcula la cantidad máxima histórica de sorteos consecutivos que cada número estuvo sin salir.
    """
    # Diccionario para guardar la demora máxima de cada número
    demora_maxima = {n: 0 for n in range(1, 26)}
    
    # Para cada número, encontrar la secuencia más larga sin aparecer
    for numero in range(1, 26):
        ultimo_indice = None
        max_sorteos = 0
        
        for i, sorteo in enumerate(sorteos):
            # Si el número sale en este sorteo
            if numero in numeros_por_sorteo[i]:
                if ultimo_indice is not None:
                    # Calcular sorteos entre apariciones (excluyendo ambos extremos)
                    sorteos_sin_aparecer = i - ultimo_indice - 1
                    max_sorteos = max(max_sorteos, sorteos_sin_aparecer)
                
                ultimo_indice = i
        
        demora_maxima[numero] = max_sorteos
    
    return demora_maxima


def calcular_promedios(numeros_por_sorteo):
    promedios = [sum(nums) / len(nums) for nums in numeros_por_sorteo]
    return promedios


def calcular_sumas(numeros_por_sorteo):
    sumas = [sum(nums) for nums in numeros_por_sorteo]
    return sumas


def calcular_coocurrencia(numeros_por_sorteo):
    pares = Counter()
    for nums in numeros_por_sorteo:
        for a, b in combinations(sorted(nums), 2):
            pares[(a, b)] += 1
    return pares


def procesar_estadisticas(fecha_limite=None, use_cache=True):
    from tombola.stats_cache import load_cached_stats, save_stats_to_cache
    
    # Intentar cargar desde caché
    if use_cache:
        cached = load_cached_stats('telekino', fecha_limite)
        if cached:
            print("📦 Cargando estadísticas desde caché...\n")
            _print_telekino_stats(cached['stats'], fecha_limite)
            return
    
    # Calcular estadísticas
    sorteos, numeros_por_sorteo = load_data(fecha_limite)

    print("\n=== CARGA DE DATOS ===")
    print(f"Sorteos cargados: {len(sorteos)}")
    if fecha_limite:
        print(f"📅 Filtrado: Solo sorteos anteriores a {fecha_limite}")
        print(f"   (útil para backtesting de estrategias)")

    frec = calcular_frecuencias(numeros_por_sorteo)
    omision = calcular_omision(sorteos, numeros_por_sorteo)
    cooc = calcular_coocurrencia(numeros_por_sorteo)
    demora_max = calcular_demora_maxima(sorteos, numeros_por_sorteo)
    
    # Preparar datos para caché
    stats_data = {
        'sorteos_count': len(sorteos),
        'frecuencias': dict(frec.most_common()),
        'omision': omision,
        'coocurrencia': {f"{a}-{b}": v for (a, b), v in cooc.most_common()},
        'demora_maxima': demora_max
    }
    
    # Guardar en caché
    if use_cache:
        save_stats_to_cache('telekino', fecha_limite, stats_data)
    
    # Imprimir estadísticas
    _print_telekino_stats(stats_data, fecha_limite)


def _print_telekino_stats(stats, fecha_limite):
    """Imprime las estadísticas de Telekino."""
    frec = stats['frecuencias']
    omision = stats['omision']
    demora_max = stats['demora_maxima']
    cooc_data = stats.get('coocurrencia', {})
    
    print("\n=== FRECUENCIAS (APARICIONES) ===")
    for n, cant in sorted(frec.items(), key=lambda x: x[1], reverse=True):
        print(f"Número {int(n)}: {cant} veces")

    print("\n=== TOP 5 - NÚMEROS CALIENTES ===")
    top_5 = sorted(frec.items(), key=lambda x: x[1], reverse=True)[:5]
    for n, cant in top_5:
        print(f"{int(n):02d} → {cant} apariciones")

    print("\n=== TOP 5 - NÚMEROS FRÍOS ===")
    bottom_5 = sorted(frec.items(), key=lambda x: x[1])[:5]
    for n, cant in bottom_5:
        print(f"{int(n):02d} → {cant} apariciones")

    print("\n=== OMISIÓN (sorteos sin aparecer) ===")
    omision_ordenada = sorted(
        [(int(n), count) for n, count in omision.items() if count > 0],
        key=lambda x: x[1],
        reverse=True
    )
    if omision_ordenada:
        for n, sorteos_omitidos in omision_ordenada:
            print(f"{n:02d}: {sorteos_omitidos}")
    else:
        print("Todos los números salieron en el último sorteo")

    print("\n=== TOP 10 - DEMORA MÁXIMA (sorteos sin aparecer) ===")
    demora_ordenada = sorted(demora_max.items(), key=lambda x: x[1], reverse=True)[:10]
    for n, sorteos_sin_salir in demora_ordenada:
        if sorteos_sin_salir > 0:
            print(f"{int(n):02d}: {sorteos_sin_salir} sorteos")

    print("\n=== TOP 10 PARES QUE MÁS SALEN JUNTOS ===")
    cooc_sorted = sorted(cooc_data.items(), key=lambda x: x[1], reverse=True)[:10]
    for pair_str, veces in cooc_sorted:
        print(f"{pair_str}: {veces} veces")



def check_repeated_combinations():
    """
    Verifica si alguna combinación de 15 números se ha repetido en la historia del Telekino.
    """
    print("\n🔍 Buscando combinaciones repetidas en todo el histórico de Telekino...")
    
    # Cargar datos sin filtrar por fecha
    sorteos, numeros_por_sorteo = load_data(fecha_limite=None)
    
    # Diccionario para rastrear combinaciones: tuple(sorted_nums) -> list of occurrences
    history = defaultdict(list)
    
    count_total = 0
    
    for i, row in enumerate(sorteos):
        fecha = row['fecha']
        nro_sorteo = row['sorteo']
        nums = tuple(sorted(numeros_por_sorteo[i]))
        
        history[nums].append({
            "fecha": fecha,
            "sorteo": nro_sorteo
        })
        count_total += 1

    print(f"Analizados {count_total} sorteos.")
    
    # Filtrar las que tienen más de 1 aparición
    repeats = {k: v for k, v in history.items() if len(v) > 1}
    
    if not repeats:
        print("\n✅ ¡Increíble! No se encontraron combinaciones repetidas en la historia del Telekino.")
    else:
        print(f"\n⚠️  Se encontraron {len(repeats)} combinaciones repetidas:\n")
        for nums, occurrences in repeats.items():
            nums_str = ", ".join(map(str, nums))
            print(f"🔢 Combinación: [{nums_str}]")
            print(f"   Apareció {len(occurrences)} veces:")
            for occ in occurrences:
                print(f"   • {occ['fecha']} (Sorteo {occ['sorteo']})")
            print("-" * 50)


if __name__ == "__main__":
    procesar_estadisticas()
