# tombola/quini6_verificar.py
import csv
from datetime import datetime

MIS_JUGADAS_PATH = "data/mis_jugadas_quini6.csv"
SORTEOS_PATH = "data/quini6.csv"


def cargar_mis_jugadas():
    """Carga las jugadas del usuario desde el CSV."""
    jugadas = []
    
    with open(MIS_JUGADAS_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            jugada = {
                'id': row['jugada_id'],
                'numeros': [int(row[f'n{i}']) for i in range(1, 7)]
            }
            jugadas.append(jugada)
    
    return jugadas


def cargar_ultimo_sorteo():
    """Carga el último sorteo de Quini 6."""
    with open(SORTEOS_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    if not rows:
        return None
    
    # Encontrar el sorteo con la fecha más reciente
    ultimo = None
    fecha_mas_reciente = None
    
    for row in rows:
        try:
            fecha = datetime.strptime(row["fecha"], "%Y-%m-%d").date()
            if fecha_mas_reciente is None or fecha > fecha_mas_reciente:
                fecha_mas_reciente = fecha
                ultimo = row
        except:
            continue
    
    if not ultimo:
        return None
    
    return {
        'sorteo': ultimo['sorteo'],
        'fecha': str(fecha_mas_reciente),
        'tradicional': [int(ultimo[f't{i}']) for i in range(1, 7)],
        'segunda': [int(ultimo[f's{i}']) for i in range(1, 7)],
        'revancha': [int(ultimo[f'r{i}']) for i in range(1, 7)],
        'siempre_sale': [int(ultimo[f'ss{i}']) for i in range(1, 7)]
    }


def contar_aciertos(jugada_numeros, sorteo_numeros):
    """Cuenta cuántos números coinciden entre la jugada y el sorteo."""
    jugada_set = set(jugada_numeros)
    sorteo_set = set(sorteo_numeros)
    aciertos = jugada_set.intersection(sorteo_set)
    return len(aciertos), sorted(aciertos)


def verificar_jugadas():
    """Verifica todas las jugadas contra el último sorteo."""
    print("🎲 VERIFICADOR DE JUGADAS QUINI 6\n")
    
    jugadas = cargar_mis_jugadas()
    sorteo = cargar_ultimo_sorteo()
    
    if not sorteo:
        print("❌ No hay sorteos guardados. Ejecuta 'python main.py quini6 scrape' primero.")
        return
    
    print(f"📅 Sorteo: {sorteo['sorteo']} - Fecha: {sorteo['fecha']}\n")
    print("="*70)
    
    # Las 4 modalidades en orden secuencial
    modalidades = [
        ('TRADICIONAL (Sub-sorteo 1)', sorteo['tradicional']),
        ('LA SEGUNDA (Sub-sorteo 2)', sorteo['segunda']),
        ('REVANCHA (Sub-sorteo 3)', sorteo['revancha']),
        ('SIEMPRE SALE (Sub-sorteo 4)', sorteo['siempre_sale'])
    ]
    
    # Resultados totales por modalidad
    resultados_totales = {
        'tradicional': {'6': 0, '5': 0, '4': 0, '3': 0},
        'segunda': {'6': 0, '5': 0, '4': 0, '3': 0},
        'revancha': {'6': 0, '5': 0, '4': 0, '3': 0},
        'siempre_sale': {'6': 0, '5': 0, '4': 0, '3': 0}
    }
    
    modalidad_keys = ['tradicional', 'segunda', 'revancha', 'siempre_sale']
    
    for idx, (nombre_modalidad, numeros_sorteo) in enumerate(modalidades):
        print(f"\n🎯 {nombre_modalidad}")
        print(f"Números sorteados: {', '.join([f'{n:02d}' for n in numeros_sorteo])}")
        print("-"*70)
        
        ganadores = []
        
        for jugada in jugadas:
            cantidad_aciertos, numeros_acertados = contar_aciertos(
                jugada['numeros'],
                numeros_sorteo
            )
            
            if cantidad_aciertos >= 3:  # Mostrar solo 3+ aciertos
                ganadores.append({
                    'id': jugada['id'],
                    'aciertos': cantidad_aciertos,
                    'numeros': numeros_acertados,
                    'jugada': jugada['numeros']
                })
            
            # Contar para estadísticas
            if cantidad_aciertos >= 3:
                modalidad_key = modalidad_keys[idx]
                resultados_totales[modalidad_key][str(cantidad_aciertos)] += 1
        
        if ganadores:
            # Ordenar por cantidad de aciertos (mayor a menor)
            ganadores.sort(key=lambda x: x['aciertos'], reverse=True)
            
            for g in ganadores:
                print(f"  ✅ Jugada #{g['id']:>2} → {g['aciertos']} aciertos")
                print(f"     Tu jugada: {', '.join([f'{n:02d}' for n in g['jugada']])}")
                print(f"     Acertaste: {', '.join([f'{n:02d}' for n in g['numeros']])}")
        else:
            print("  ❌ Sin aciertos significativos (menos de 3)")
    
    # Resumen final
    print("\n" + "="*70)
    print("📊 RESUMEN DE ACIERTOS")
    print("="*70)
    
    modalidades_nombres = [
        ('tradicional', 'TRADICIONAL'),
        ('segunda', 'LA SEGUNDA'),
        ('revancha', 'REVANCHA'),
        ('siempre_sale', 'SIEMPRE SALE')
    ]
    
    hay_premios = False
    for key, nombre in modalidades_nombres:
        if any(resultados_totales[key].values()):
            print(f"\n{nombre}:")
            if resultados_totales[key]['6'] > 0:
                print(f"  🏆 6 aciertos: {resultados_totales[key]['6']} jugada(s) - ¡PRIMER PREMIO!")
                hay_premios = True
            if resultados_totales[key]['5'] > 0:
                print(f"  🥈 5 aciertos: {resultados_totales[key]['5']} jugada(s) - ¡SEGUNDO PREMIO!")
                hay_premios = True
            if resultados_totales[key]['4'] > 0:
                print(f"  🥉 4 aciertos: {resultados_totales[key]['4']} jugada(s) - ¡TERCER PREMIO!")
                hay_premios = True
            if resultados_totales[key]['3'] > 0:
                print(f"  📌 3 aciertos: {resultados_totales[key]['3']} jugada(s)")
    
    if not hay_premios:
        print("\n😔 No hubo premios en este sorteo. ¡Mejor suerte la próxima!")
    else:
        print("\n🎉 ¡FELICITACIONES! Tuviste aciertos premiados.")
    
    # Información adicional sobre el orden secuencial
    print("\n" + "="*70)
    print("ℹ️  NOTA: Las modalidades se procesan en orden secuencial:")
    print("   1️⃣  Tradicional → 2️⃣  La Segunda → 3️⃣  Revancha → 4️⃣  Siempre Sale")
    print("   Puedes ganar en múltiples modalidades con la misma jugada!")


if __name__ == "__main__":
    verificar_jugadas()
