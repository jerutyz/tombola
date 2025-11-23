# analysis/visualizacion_telekino.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter
import csv
from datetime import datetime
import os

CSV_PATH = "data/telekino.csv"
OUTPUT_DIR = "visualizaciones"


def cargar_datos(fecha_limite=None):
    """Carga los datos de Telekino, opcionalmente hasta una fecha límite."""
    sorteos = []
    numeros_por_sorteo = []

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filtrar por fecha si se proporciona
            if fecha_limite:
                if hasattr(fecha_limite, 'strftime'):
                    fecha_limite_str = fecha_limite.strftime('%Y-%m-%d')
                else:
                    fecha_limite_str = str(fecha_limite)
                
                if row.get('fecha', '') > fecha_limite_str:
                    continue
            
            sorteos.append(row)
            nums = [int(row[f"n{i}"]) for i in range(1, 16)]
            numeros_por_sorteo.append(nums)

    return sorteos, numeros_por_sorteo


def crear_mapa_calor_frecuencias(numeros_por_sorteo, sorteos_count):
    """Crea un mapa de calor de frecuencias para Telekino."""
    # Contar frecuencias
    frecuencias = Counter()
    for nums in numeros_por_sorteo:
        frecuencias.update(nums)
    
    # Crear matriz 5x5 (1-25)
    matriz = np.zeros((5, 5))
    
    for num in range(1, 26):
        fila = (num - 1) // 5
        col = (num - 1) % 5
        matriz[fila, col] = frecuencias.get(num, 0) / sorteos_count * 100  # Porcentaje
    
    # Crear figura
    plt.figure(figsize=(12, 10))
    
    # Mapa de calor
    ax = sns.heatmap(
        matriz,
        annot=False,
        fmt='.1f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Frecuencia (%)'},
        linewidths=1,
        linecolor='gray',
        square=True
    )
    
    # Añadir números en cada celda
    for fila in range(5):
        for col in range(5):
            num = fila * 5 + col + 1
            freq_pct = matriz[fila, col]
            freq_count = int(frecuencias.get(num, 0))
            
            # Color del texto basado en la intensidad
            color = 'white' if freq_pct > 50 else 'black'
            
            ax.text(
                col + 0.5,
                fila + 0.3,
                f'{num:02d}',
                ha='center',
                va='center',
                fontsize=18,
                fontweight='bold',
                color=color
            )
            ax.text(
                col + 0.5,
                fila + 0.7,
                f'{freq_count}',
                ha='center',
                va='center',
                fontsize=12,
                color=color
            )
    
    plt.title(f'Mapa de Calor - Telekino\n(Frecuencia de aparición en {sorteos_count} sorteos)', 
              fontsize=18, fontweight='bold', pad=20)
    plt.xlabel('')
    plt.ylabel('')
    plt.xticks([])
    plt.yticks([])
    
    plt.tight_layout()
    return plt.gcf()


def crear_grafico_omision(numeros_por_sorteo):
    """Crea un gráfico de barras de omisión para Telekino."""
    # Calcular omisión
    ultimas_apariciones = {n: None for n in range(1, 26)}
    
    for idx, nums in enumerate(reversed(numeros_por_sorteo)):
        for n in nums:
            if ultimas_apariciones[n] is None:
                ultimas_apariciones[n] = idx
    
    for n in ultimas_apariciones:
        if ultimas_apariciones[n] is None:
            ultimas_apariciones[n] = len(numeros_por_sorteo)
    
    # Filtrar solo los que tienen omisión > 0 y ordenar
    omision_filtrada = {k: v for k, v in ultimas_apariciones.items() if v > 0}
    omision_ordenada = sorted(omision_filtrada.items(), key=lambda x: x[1], reverse=True)
    
    if not omision_ordenada:
        omision_ordenada = [(1, 0)]  # Placeholder
    
    # Tomar solo los top 15
    omision_top = omision_ordenada[:15]
    
    numeros = [f'{n:02d}' for n, _ in omision_top]
    valores = [v for _, v in omision_top]
    
    # Crear gráfico
    plt.figure(figsize=(14, 6))
    
    colors = sns.color_palette("Reds_r", len(numeros))
    bars = plt.bar(numeros, valores, color=colors, edgecolor='black', linewidth=1)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold'
        )
    
    plt.title(f'Top 15 Números con Mayor Omisión - Telekino\n(Sorteos sin aparecer)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Número', fontsize=13, fontweight='bold')
    plt.ylabel('Sorteos sin aparecer', fontsize=13, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return plt.gcf()


def crear_grafico_top_numeros(numeros_por_sorteo, sorteos_count):
    """Crea un gráfico de barras con los números más frecuentes."""
    # Contar frecuencias
    frecuencias = Counter()
    for nums in numeros_por_sorteo:
        frecuencias.update(nums)
    
    # Top 15
    top15 = frecuencias.most_common(15)
    
    numeros = [f'{n:02d}' for n, _ in top15]
    valores = [c for _, c in top15]
    
    # Crear gráfico
    plt.figure(figsize=(14, 6))
    
    colors = sns.color_palette("Greens_r", len(numeros))
    bars = plt.bar(numeros, valores, color=colors, edgecolor='black', linewidth=1)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=11,
            fontweight='bold'
        )
    
    plt.title(f'Top 15 Números Más Frecuentes - Telekino\n({sorteos_count} sorteos)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Número', fontsize=13, fontweight='bold')
    plt.ylabel('Apariciones', fontsize=13, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return plt.gcf()


def crear_visualizaciones():
    """Crea todas las visualizaciones de Telekino y las guarda."""
    print("📊 Generando visualizaciones de Telekino...\n")
    
    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Cargar datos
    sorteos, numeros_por_sorteo = cargar_datos()
    sorteos_count = len(sorteos)
    
    print(f"Sorteos cargados: {sorteos_count}\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Mapa de calor de frecuencias
    print("Generando mapa de calor...")
    fig_freq = crear_mapa_calor_frecuencias(numeros_por_sorteo, sorteos_count)
    filename_freq = f"{OUTPUT_DIR}/telekino_mapa_calor_{timestamp}.png"
    fig_freq.savefig(filename_freq, dpi=300, bbox_inches='tight')
    print(f"  ✅ {filename_freq}")
    plt.close(fig_freq)
    
    # Gráfico de omisión
    print("Generando gráfico de omisión...")
    fig_omision = crear_grafico_omision(numeros_por_sorteo)
    filename_omision = f"{OUTPUT_DIR}/telekino_omision_{timestamp}.png"
    fig_omision.savefig(filename_omision, dpi=300, bbox_inches='tight')
    print(f"  ✅ {filename_omision}")
    plt.close(fig_omision)
    
    # Gráfico de top números
    print("Generando gráfico de top números...")
    fig_top = crear_grafico_top_numeros(numeros_por_sorteo, sorteos_count)
    filename_top = f"{OUTPUT_DIR}/telekino_top_frecuentes_{timestamp}.png"
    fig_top.savefig(filename_top, dpi=300, bbox_inches='tight')
    print(f"  ✅ {filename_top}")
    plt.close(fig_top)
    
    print(f"\n🎉 Visualizaciones guardadas en '{OUTPUT_DIR}/'")
    print(f"   Total: 3 imágenes generadas")


if __name__ == "__main__":
    crear_visualizaciones()
