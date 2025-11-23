#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import warnings
from datetime import datetime, timedelta
# Suprimir warning de urllib3/OpenSSL
warnings.filterwarnings('ignore', message='urllib3 v2 only supports OpenSSL 1.1.1+')
warnings.filterwarnings("ignore", message=".*NotOpenSSLWarning.*")


from tombola.telekino import Telekino
from analysis.simulator import run_simulations
from tombola.telekino_scraper import (
    fetch_last_sorteo, save_to_csv, get_last_saved_sorteo, 
    previous_telekino_date, fetch_sorteo, get_all_saved_sorteos,
    next_telekino_date, get_last_sunday, get_first_saved_sorteo
)
from tombola.telekino import procesar_estadisticas

# Quini 6 imports
from tombola.quini6 import Quini6, procesar_estadisticas as procesar_estadisticas_quini6
import tombola.quini6_scraper as q6_scraper
from tombola.quini6_verificar import verificar_jugadas


def simulate():
    game = Telekino()

    print("Simulando Telekino...")
    stats = run_simulations(game, n=5000)

    top10 = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:10]

    print("\nTop 10 números más frecuentes:")
    for num, count in top10:
        print(f"{num}: {count}")


def scrape_latest():
    print("Buscando próximo sorteo faltante...")
    
    # Obtener todas las fechas ya guardadas
    saved_dates = get_all_saved_sorteos()
    
    # Obtener el último domingo disponible
    last_sunday = get_last_sunday()
    
    # Si es hoy mismo, retroceder una semana (el sorteo de hoy no está disponible aún)
    if last_sunday == datetime.now().date():
        last_sunday = previous_telekino_date(last_sunday)
    
    # Obtener el último sorteo guardado
    last_saved = get_last_saved_sorteo()
    
    if last_saved:
        next_date = next_telekino_date(last_saved["fecha"])
        
        # Verificar si ya estamos actualizados hacia adelante
        if next_date > last_sunday:
            print(f"✓ Ya tienes todos los sorteos recientes hasta {last_saved['fecha']}")
            print(f"\n📅 Buscando sorteos históricos más antiguos...")
            
            # Buscar hacia atrás
            first_saved = get_first_saved_sorteo()
            if first_saved:
                prev_date = previous_telekino_date(first_saved["fecha"])
                print(f"Primer sorteo guardado: {first_saved['sorteo']} - fecha {first_saved['fecha']}")
                print(f"Buscando sorteo anterior → {prev_date}")
                
                result = fetch_sorteo(prev_date)
                if result:
                    save_to_csv(result)
                    print(f"\n✅ Sorteo {result['sorteo']} ({prev_date}) guardado exitosamente")
                else:
                    print(f"\n⚠️  No se encontró sorteo para {prev_date}")
                    print(f"Puede que no esté disponible en la web.")
            return
        
        print(f"Último guardado: sorteo {last_saved['sorteo']} - fecha {last_saved['fecha']}")
        print(f"Buscando siguiente sorteo → {next_date}")
    else:
        print("No hay CSV, buscando el último sorteo disponible...")
        next_date = last_sunday
    
    # Verificar si ya está guardado (por si acaso)
    if next_date in saved_dates:
        print(f"✓ El sorteo del {next_date} ya está guardado")
        return
    
    # Buscar el sorteo
    print(f"\n🔍 Buscando sorteo del {next_date}...")
    result = fetch_sorteo(next_date)
    
    if result:
        save_to_csv(result)
        print(f"\n✅ Sorteo {result['sorteo']} ({next_date}) guardado exitosamente")
    else:
        print(f"\n⚠️  No se encontró el sorteo para {next_date}")
        print(f"Puede que aún no esté publicado en la web.")

def scrape_quini6():
    print("Buscando próximo sorteo Quini 6 faltante...")
    
    saved_dates = q6_scraper.get_all_saved_sorteos()
    last_quini6_date = q6_scraper.get_last_quini6_date()
    
    # Si es hoy, puede que no esté publicado aún
    if last_quini6_date == datetime.now().date():
        last_quini6_date = q6_scraper.previous_quini6_date(last_quini6_date)
    
    last_saved = q6_scraper.get_last_saved_sorteo()
    
    if last_saved:
        next_date = q6_scraper.next_quini6_date(last_saved["fecha"])
        
        # Verificar si ya estamos actualizados
        if next_date > last_quini6_date:
            print(f"✓ Ya tienes todos los sorteos recientes hasta {last_saved['fecha']}")
            print(f"\n📅 Buscando sorteos históricos más antiguos...")
            
            first_saved = q6_scraper.get_first_saved_sorteo()
            if first_saved:
                prev_date = q6_scraper.previous_quini6_date(first_saved["fecha"])
                
                # Verificar si está en la lista de excluidos
                if q6_scraper.is_fecha_excluida(prev_date):
                    print(f"⏭️  Fecha {prev_date} está marcada como sin sorteo, saltando...")
                    # Intentar con la fecha anterior
                    prev_date = q6_scraper.previous_quini6_date(prev_date)
                
                print(f"Primer sorteo guardado: {first_saved['sorteo']} - fecha {first_saved['fecha']}")
                print(f"Buscando sorteo anterior → {prev_date}")
                
                result = q6_scraper.fetch_sorteo(prev_date)
                if result:
                    q6_scraper.save_to_csv(result)
                    print(f"\n✅ Sorteo {result['sorteo']} ({prev_date}) guardado exitosamente")
                else:
                    print(f"\n⚠️  No se encontró sorteo para {prev_date}")
                    print(f"\n❓ Esto puede deberse a:")
                    print(f"   • Feriado o día sin sorteo")
                    print(f"   • El sorteo aún no está publicado")
                    print(f"   • Error en la página web")
                    
                    respuesta = input(f"\n¿Marcar {prev_date} como fecha sin sorteo y continuar? (s/n): ").lower().strip()
                    
                    if respuesta == 's' or respuesta == 'si':
                        q6_scraper.agregar_fecha_excluida(prev_date)
                        print(f"✓ Fecha {prev_date} agregada a fechas excluidas")
                        print(f"💡 Ejecuta el comando nuevamente para continuar con la fecha anterior")
                    else:
                        print("⏸️  Scraping detenido. Ejecuta el comando cuando el sorteo esté disponible.")
            return
        
        print(f"Último guardado: sorteo {last_saved['sorteo']} - fecha {last_saved['fecha']}")
        print(f"Buscando siguiente sorteo → {next_date}")
    else:
        print("No hay CSV, buscando el último sorteo disponible...")
        next_date = last_quini6_date
    
    if next_date in saved_dates:
        print(f"✓ El sorteo del {next_date} ya está guardado")
        return
    
    print(f"\n🔍 Buscando sorteo del {next_date}...")
    result = q6_scraper.fetch_sorteo(next_date)
    
    if result:
        q6_scraper.save_to_csv(result)
        print(f"\n✅ Sorteo {result['sorteo']} ({next_date}) guardado exitosamente")
    else:
        print(f"\n⚠️  No se encontró el sorteo para {next_date}")

def telekino_stats(fecha_limite=None):
    procesar_estadisticas(fecha_limite)

def telekino_visualizar():
    from analysis.visualizacion_telekino import crear_visualizaciones as crear_visualizaciones_telekino
    crear_visualizaciones_telekino()

def quini6_stats(fecha_limite=None):
    procesar_estadisticas_quini6(fecha_limite)

def quini6_verificar():
    verificar_jugadas()

def quini6_visualizar():
    from analysis.visualizacion_quini6 import crear_visualizaciones
    crear_visualizaciones()

def help():
    print("""
Comandos disponibles:

  TELEKINO:
  python main.py telekino scrape              → scrapea el último sorteo disponible
  python main.py telekino stats [YYYY-MM-DD]  → calcula estadísticas del Telekino
  python main.py telekino visualizar          → genera mapas de calor y gráficos
  python main.py telekino simulate            → corre simulación Monte Carlo
  
  QUINI 6:
  python main.py quini6 scrape                → scrapea el último sorteo Quini 6
  python main.py quini6 stats [YYYY-MM-DD]    → calcula estadísticas del Quini 6
  python main.py quini6 verificar             → verifica tus jugadas contra el último sorteo
  python main.py quini6 visualizar            → genera mapas de calor y gráficos
  
  📅 BACKTESTING:
  Agrega una fecha opcional a 'stats' para ver estadísticas históricas.
  Ejemplo: python main.py quini6 stats 2024-11-20
  Esto mostrará estadísticas usando solo sorteos anteriores a 2024-11-20.
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        help()
        sys.exit(0)

    # Nuevo parser jerárquico: game command
    game = sys.argv[1].lower()
    
    if game in ["help", "-h", "--help"]:
        help()
        sys.exit(0)
    
    if len(sys.argv) < 3:
        print(f"❌ Error: Especifica un comando para '{game}'")
        print(f"Ejemplo: python main.py {game} scrape")
        print("\nUsa 'python main.py help' para ver todos los comandos")
        sys.exit(1)
    
    command = sys.argv[2].lower()
    
    # Verificar si hay un tercer argumento (fecha para stats)
    fecha_arg = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Telekino commands
    if game == "telekino":
        if command == "scrape":
            scrape_latest()
        elif command == "stats":
            telekino_stats(fecha_arg)
        elif command == "visualizar":
            telekino_visualizar()
        elif command == "simulate":
            simulate()
        else:
            print(f"❌ Comando '{command}' no válido para telekino")
            print("Comandos válidos: scrape, stats [YYYY-MM-DD], visualizar, simulate")
            sys.exit(1)
    
    # Quini 6 commands
    elif game == "quini6":
        if command == "scrape":
            scrape_quini6()
        elif command == "stats":
            quini6_stats(fecha_arg)
        elif command == "verificar":
            quini6_verificar()
        elif command == "visualizar":
            quini6_visualizar()
        else:
            print(f"❌ Comando '{command}' no válido para quini6")
            print("Comandos válidos: scrape, stats [YYYY-MM-DD], verificar, visualizar")
            sys.exit(1)
    
    else:
        print(f"❌ Juego '{game}' no reconocido")
        print("Juegos disponibles: telekino, quini6")
        print("\nUsa 'python main.py help' para ver todos los comandos")
        sys.exit(1)
