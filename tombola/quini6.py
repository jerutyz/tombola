# tombola/quini6.py
import csv
from collections import Counter, defaultdict
from itertools import combinations
import random
from .base_game import BaseGame
from config import DATA_DIR

CSV_PATH = f"{DATA_DIR}/quini6.csv"



class Quini6(BaseGame):
    def draw(self):
        """Devuelve un sorteo aleatorio de 6 números entre 0 y 45."""
        return sorted(random.sample(range(0, 46), 6))

    def num_range(self):
        """Devuelve el rango total de números válidos del juego."""
        return range(0, 46)

    def picks(self):
        """Devuelve cuántos números se sortean."""
        return 6


def load_data(fecha_limite=None):
    """
    Devuelve:
    - lista de sorteos (dicts)
    - lista de números por sorteo (ahora cada sorteo tiene 4 sub-sorteos en orden)
    
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
            
            # Cada sorteo genera 4 sub-sorteos en orden:
            # 1. Tradicional, 2. La Segunda, 3. Revancha, 4. Siempre Sale
            tradicional = [int(row[f"t{i}"]) for i in range(1, 7)]
            segunda = [int(row[f"s{i}"]) for i in range(1, 7)]
            revancha = [int(row[f"r{i}"]) for i in range(1, 7)]
            siempre_sale = [int(row[f"ss{i}"]) for i in range(1, 7)]
            
            # Agregar los 4 sub-sorteos en orden
            numeros_por_sorteo.append(tradicional)
            numeros_por_sorteo.append(segunda)
            numeros_por_sorteo.append(revancha)
            numeros_por_sorteo.append(siempre_sale)

    return sorteos, numeros_por_sorteo


def calcular_frecuencias(numeros_por_sorteo):
    counter = Counter()
    for nums in numeros_por_sorteo:
        counter.update(nums)
    return counter


def calcular_omision(numeros_por_sorteo):
    """
    Omisión = hace cuántos sub-sorteos no apareció cada número del 0 al 45.
    Cuenta desde el sub-sorteo más reciente hacia atrás.
    """
    ultimas_apariciones = {n: None for n in range(0, 46)}

    # Recorrer desde el sub-sorteo MÁS RECIENTE hacia el más antiguo
    for idx, nums in enumerate(reversed(numeros_por_sorteo)):
        for n in nums:
            if ultimas_apariciones[n] is None:
                ultimas_apariciones[n] = idx

    # Reemplazar None por "nunca apareció"
    for n in ultimas_apariciones:
        if ultimas_apariciones[n] is None:
            ultimas_apariciones[n] = len(numeros_por_sorteo)

    return ultimas_apariciones


def calcular_coocurrencia(numeros_por_sorteo):
    pares = Counter()
    for nums in numeros_por_sorteo:
        for a, b in combinations(sorted(nums), 2):
            pares[(a, b)] += 1
    return pares


def calcular_demora_maxima(numeros_por_sorteo):
    """
    Calcula la cantidad máxima de sub-sorteos consecutivos que cada número estuvo sin salir.
    """
    # Diccionario para guardar la demora máxima de cada número
    demora_maxima = {n: 0 for n in range(0, 46)}
    
    # Para cada número, encontrar la secuencia más larga sin aparecer
    for numero in range(0, 46):
        ultimo_indice = None
        max_sorteos = 0
        
        for i in range(len(numeros_por_sorteo)):
            # Si el número sale en este sub-sorteo
            if numero in numeros_por_sorteo[i]:
                if ultimo_indice is not None:
                    # Calcular sub-sorteos entre apariciones (excluyendo ambos extremos)
                    sorteos_sin_aparecer = i - ultimo_indice - 1
                    max_sorteos = max(max_sorteos, sorteos_sin_aparecer)
                
                ultimo_indice = i
        
        demora_maxima[numero] = max_sorteos
    
    return demora_maxima


def procesar_estadisticas(fecha_limite=None, use_cache=True):
    from tombola.stats_cache import load_cached_stats, save_stats_to_cache
    
    # Intentar cargar desde caché
    if use_cache:
        cached = load_cached_stats('quini6', fecha_limite)
        if cached:
            print("📦 Cargando estadísticas desde caché...\n")
            _print_quini6_stats(cached['stats'], fecha_limite)
            return
    
    # Calcular estadísticas
    sorteos, numeros_por_sorteo = load_data(fecha_limite)

    print("\n=== CARGA DE DATOS ===")
    print(f"Sorteos cargados: {len(sorteos)}")
    print(f"Sub-sorteos totales: {len(numeros_por_sorteo)} (4 por sorteo)")
    if fecha_limite:
        print(f"📅 Filtrado: Solo sorteos anteriores a {fecha_limite}")
        print(f"   (útil para backtesting de estrategias)")

    frec = calcular_frecuencias(numeros_por_sorteo)
    omision = calcular_omision(numeros_por_sorteo)
    cooc = calcular_coocurrencia(numeros_por_sorteo)
    demora_max = calcular_demora_maxima(numeros_por_sorteo)
    
    # Preparar datos para caché
    stats_data = {
        'sorteos_count': len(sorteos),
        'subsorteos_count': len(numeros_por_sorteo),
        'frecuencias': dict(frec.most_common()),
        'omision': omision,
        'coocurrencia': {f"{a}-{b}": v for (a, b), v in cooc.most_common()},
        'demora_maxima': demora_max
    }
    
    # Guardar en caché
    if use_cache:
        save_stats_to_cache('quini6', fecha_limite, stats_data)
    
    # Imprimir estadísticas
    _print_quini6_stats(stats_data, fecha_limite)


def _print_quini6_stats(stats, fecha_limite):
    """Imprime las estadísticas de Quini 6."""
    frec = stats['frecuencias']
    omision = stats['omision']
    demora_max = stats['demora_maxima']
    cooc_data = stats.get('coocurrencia', {})
    
    print("\n=== TOP 10 - NÚMEROS CALIENTES ===")
    top_freq = sorted(frec.items(), key=lambda x: x[1], reverse=True)[:10]
    for n, cant in top_freq:
        print(f"{int(n):02d} → {cant} apariciones")

    print("\n=== TOP 10 - NÚMEROS FRÍOS ===")
    bottom_freq = sorted(frec.items(), key=lambda x: x[1])[:10]
    for n, cant in bottom_freq:
        print(f"{int(n):02d} → {cant} apariciones")

    print("\n=== OMISIÓN (sub-sorteos sin aparecer) ===")
    omision_ordenada = sorted(
        [(int(n), count) for n, count in omision.items() if count > 0],
        key=lambda x: x[1],
        reverse=True
    )
    if omision_ordenada:
        for n, sorteos_omitidos in omision_ordenada[:15]:
            print(f"{n:02d}: {sorteos_omitidos} sub-sorteos")
    else:
        print("Todos los números salieron en el último sub-sorteo")

    print("\n=== TOP 10 - DEMORA MÁXIMA (sub-sorteos sin aparecer) ===")
    demora_ordenada = sorted(demora_max.items(), key=lambda x: x[1], reverse=True)[:10]
    for n, sorteos_sin_salir in demora_ordenada:
        if sorteos_sin_salir > 0:
            print(f"{int(n):02d}: {sorteos_sin_salir} sub-sorteos")

    print("\n=== TOP 10 PARES QUE MÁS SALEN JUNTOS ===")
    cooc_sorted = sorted(cooc_data.items(), key=lambda x: x[1], reverse=True)[:10]
    for pair_str, veces in cooc_sorted:
        print(f"{pair_str}: {veces} veces")



def check_repeated_combinations():
    """
    Verifica si alguna combinación de 6 números se ha repetido en la historia.
    Revisa todas las modalidades: Tradicional, Segunda, Revancha, Siempre Sale.
    """
    print("\n🔍 Buscando combinaciones repetidas en todo el histórico...")
    
    # Cargar datos sin filtrar por fecha
    sorteos, _ = load_data(fecha_limite=None)
    
    # Diccionario para rastrear combinaciones: tuple(sorted_nums) -> list of occurrences
    # Cada ocurrencia será un dict con detalles: {fecha, sorteo, modalidad}
    history = defaultdict(list)
    
    modalities = ["Tradicional", "La Segunda", "Revancha", "Siempre Sale"]
    
    count_total = 0
    
    for row in sorteos:
        fecha = row['fecha']
        nro_sorteo = row['sorteo']
        
        # Extraer las 4 combinaciones del sorteo
        combs = []
        combs.append(tuple(sorted([int(row[f"t{i}"]) for i in range(1, 7)])))
        combs.append(tuple(sorted([int(row[f"s{i}"]) for i in range(1, 7)])))
        combs.append(tuple(sorted([int(row[f"r{i}"]) for i in range(1, 7)])))
        combs.append(tuple(sorted([int(row[f"ss{i}"]) for i in range(1, 7)])))
        
        for i, nums in enumerate(combs):
            modality = modalities[i]
            history[nums].append({
                "fecha": fecha,
                "sorteo": nro_sorteo,
                "modalidad": modality
            })
            count_total += 1

    print(f"Analizadas {count_total} jugadas individuales en {len(sorteos)} sorteos.")
    
    # Filtrar las que tienen más de 1 aparición
    repeats = {k: v for k, v in history.items() if len(v) > 1}
    
    if not repeats:
        print("\n✅ ¡Increíble! No se encontraron combinaciones repetidas en la historia.")
    else:
        print(f"\n⚠️  Se encontraron {len(repeats)} combinaciones repetidas:\n")
        for nums, occurrences in repeats.items():
            nums_str = ", ".join(map(str, nums))
            print(f"🔢 Combinación: [{nums_str}]")
            print(f"   Apareció {len(occurrences)} veces:")
            for occ in occurrences:
                print(f"   • {occ['fecha']} (Sorteo {occ['sorteo']}) - {occ['modalidad']}")
            print("-" * 50)


if __name__ == "__main__":
    procesar_estadisticas()
