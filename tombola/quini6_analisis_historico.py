# tombola/quini6_analisis_historico.py
import csv
from datetime import datetime
from collections import defaultdict

MIS_JUGADAS_PATH = "data/mis_jugadas_quini6.csv"
SORTEOS_PATH = "data/quini6.csv"


def cargar_mis_jugadas():
    """Carga las jugadas del usuario desde el CSV."""
    jugadas = []
    
    with open(MIS_JUGADAS_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('jugada_id'):  # Skip empty rows
                continue
            jugada = {
                'id': row['jugada_id'],
                'numeros': [int(row[f'n{i}']) for i in range(1, 7)]
            }
            jugadas.append(jugada)
    
    return jugadas


def cargar_todos_sorteos():
    """Carga todos los sorteos históricos de Quini 6."""
    sorteos = []
    
    with open(SORTEOS_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('sorteo'):  # Skip empty rows
                continue
            
            try:
                fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
                
                sorteo = {
                    'sorteo': row['sorteo'],
                    'fecha': str(fecha),
                    'tradicional': [int(row[f't{i}']) for i in range(1, 7)],
                    'segunda': [int(row[f's{i}']) for i in range(1, 7)],
                    'revancha': [int(row[f'r{i}']) for i in range(1, 7)],
                    'siempre_sale': [int(row[f'ss{i}']) for i in range(1, 7)]
                }
                sorteos.append(sorteo)
            except (ValueError, KeyError):
                continue
    
    # Ordenar por fecha (más recientes primero)
    sorteos.sort(key=lambda x: x['fecha'], reverse=True)
    
    return sorteos


def contar_aciertos(jugada_numeros, sorteo_numeros):
    """Cuenta cuántos números coinciden entre la jugada y el sorteo."""
    jugada_set = set(jugada_numeros)
    sorteo_set = set(sorteo_numeros)
    aciertos = jugada_set.intersection(sorteo_set)
    return len(aciertos), sorted(aciertos)


def analizar_historico():
    """Analiza todos los sorteos históricos en busca de 5 y 6 aciertos."""
    print("🔍 ANÁLISIS HISTÓRICO DE ACIERTOS - QUINI 6\n")
    print("="*80)
    
    jugadas = cargar_mis_jugadas()
    sorteos = cargar_todos_sorteos()
    
    if not sorteos:
        print("❌ No hay sorteos guardados. Ejecuta 'python main.py quini6 scrape' primero.")
        return
    
    print(f"📊 Analizando {len(jugadas)} jugadas contra {len(sorteos)} sorteos...")
    print(f"📅 Rango de fechas: {sorteos[-1]['fecha']} hasta {sorteos[0]['fecha']}\n")
    print("="*80)
    
    # Estructura para almacenar resultados
    resultados_6 = defaultdict(list)  # {jugada_id: [(fecha, sorteo, modalidad, numeros_acertados)]}
    resultados_5 = defaultdict(list)
    
    modalidades_info = [
        ('tradicional', 'TRADICIONAL'),
        ('segunda', 'LA SEGUNDA'),
        ('revancha', 'REVANCHA'),
        ('siempre_sale', 'SIEMPRE SALE')
    ]
    
    # Analizar cada sorteo
    for sorteo in sorteos:
        for jugada in jugadas:
            for modalidad_key, modalidad_nombre in modalidades_info:
                numeros_sorteo = sorteo[modalidad_key]
                cantidad_aciertos, numeros_acertados = contar_aciertos(
                    jugada['numeros'],
                    numeros_sorteo
                )
                
                if cantidad_aciertos == 6:
                    resultados_6[jugada['id']].append({
                        'fecha': sorteo['fecha'],
                        'sorteo': sorteo['sorteo'],
                        'modalidad': modalidad_nombre,
                        'numeros_acertados': numeros_acertados,
                        'jugada_completa': jugada['numeros']
                    })
                elif cantidad_aciertos == 5:
                    resultados_5[jugada['id']].append({
                        'fecha': sorteo['fecha'],
                        'sorteo': sorteo['sorteo'],
                        'modalidad': modalidad_nombre,
                        'numeros_acertados': numeros_acertados,
                        'jugada_completa': jugada['numeros']
                    })
    
    # Mostrar resultados de 6 aciertos
    print("\n🏆 RESULTADOS CON 6 ACIERTOS (¡PRIMER PREMIO!)")
    print("="*80)
    
    if resultados_6:
        total_premios_6 = sum(len(aciertos) for aciertos in resultados_6.values())
        print(f"🎉 ¡Encontrados {total_premios_6} caso(s) de 6 aciertos!\n")
        
        for jugada_id in sorted(resultados_6.keys()):
            aciertos = resultados_6[jugada_id]
            # Ordenar por fecha (más reciente primero)
            aciertos.sort(key=lambda x: x['fecha'], reverse=True)
            
            print(f"Jugada #{jugada_id}: {', '.join([f'{n:02d}' for n in aciertos[0]['jugada_completa']])}")
            print(f"  Total de ocurrencias: {len(aciertos)}")
            
            for i, resultado in enumerate(aciertos, 1):
                if i == 1:
                    print(f"  📅 Última vez: {resultado['fecha']} (Sorteo {resultado['sorteo']}) - {resultado['modalidad']}")
                    print(f"     Números acertados: {', '.join([f'{n:02d}' for n in resultado['numeros_acertados']])}")
                else:
                    print(f"  📅 También en: {resultado['fecha']} (Sorteo {resultado['sorteo']}) - {resultado['modalidad']}")
            print()
    else:
        print("😔 No se encontraron casos de 6 aciertos en el periodo analizado.\n")
    
    # Mostrar resultados de 5 aciertos
    print("\n🥈 RESULTADOS CON 5 ACIERTOS (SEGUNDO PREMIO)")
    print("="*80)
    
    if resultados_5:
        total_premios_5 = sum(len(aciertos) for aciertos in resultados_5.values())
        print(f"👏 ¡Encontrados {total_premios_5} caso(s) de 5 aciertos!\n")
        
        for jugada_id in sorted(resultados_5.keys()):
            aciertos = resultados_5[jugada_id]
            # Ordenar por fecha (más reciente primero)
            aciertos.sort(key=lambda x: x['fecha'], reverse=True)
            
            print(f"Jugada #{jugada_id}: {', '.join([f'{n:02d}' for n in aciertos[0]['jugada_completa']])}")
            print(f"  Total de ocurrencias: {len(aciertos)}")
            
            # Mostrar solo las 3 más recientes si hay muchas
            ocurrencias_a_mostrar = min(3, len(aciertos))
            for i, resultado in enumerate(aciertos[:ocurrencias_a_mostrar], 1):
                if i == 1:
                    print(f"  📅 Última vez: {resultado['fecha']} (Sorteo {resultado['sorteo']}) - {resultado['modalidad']}")
                    print(f"     Números acertados: {', '.join([f'{n:02d}' for n in resultado['numeros_acertados']])}")
                else:
                    print(f"  📅 También en: {resultado['fecha']} (Sorteo {resultado['sorteo']}) - {resultado['modalidad']}")
            
            if len(aciertos) > 3:
                print(f"  ... y {len(aciertos) - 3} ocurrencia(s) más")
            print()
    else:
        print("😔 No se encontraron casos de 5 aciertos en el periodo analizado.\n")
    
    # Resumen final
    print("="*80)
    print("📊 RESUMEN GENERAL")
    print("="*80)
    print(f"Total de jugadas analizadas: {len(jugadas)}")
    print(f"Total de sorteos analizados: {len(sorteos)}")
    print(f"Jugadas con 6 aciertos: {len(resultados_6)} ({sum(len(a) for a in resultados_6.values())} ocurrencias)")
    print(f"Jugadas con 5 aciertos: {len(resultados_5)} ({sum(len(a) for a in resultados_5.values())} ocurrencias)")
    print("="*80)


if __name__ == "__main__":
    analizar_historico()
