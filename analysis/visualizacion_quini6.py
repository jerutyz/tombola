# analysis/visualizacion_quini6.py
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter
import csv
from datetime import datetime
import os
import sys

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, VISUALIZACIONES_DIR

CSV_PATH = f"{DATA_DIR}/quini6.csv"
OUTPUT_DIR = VISUALIZACIONES_DIR


def cargar_datos(fecha_limite=None):
    """Carga los datos de Quini 6 como sub-sorteos secuenciales, opcionalmente hasta una fecha límite."""
    sorteos = []
    numeros_por_subsorteo = []

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
            
            # Cada sorteo genera 4 sub-sorteos en orden:
            tradicional = [int(row[f"t{i}"]) for i in range(1, 7)]
            segunda = [int(row[f"s{i}"]) for i in range(1, 7)]
            revancha = [int(row[f"r{i}"]) for i in range(1, 7)]
            siempre_sale = [int(row[f"ss{i}"]) for i in range(1, 7)]
            
            numeros_por_subsorteo.append(tradicional)
            numeros_por_subsorteo.append(segunda)
            numeros_por_subsorteo.append(revancha)
            numeros_por_subsorteo.append(siempre_sale)

    return sorteos, numeros_por_subsorteo


def crear_mapa_calor_frecuencias(numeros_por_subsorteo, sorteos_count):
    """Crea un mapa de calor de frecuencias para Quini 6."""
    # Contar frecuencias
    frecuencias = Counter()
    for nums in numeros_por_subsorteo:
        frecuencias.update(nums)
    
    # Crear matriz 5x10 (0-45 = 46 números, formato 0-49 para visual)
    matriz = np.zeros((5, 10))
    
    for num in range(50):
        if num <= 45:
            fila = num // 10
            col = num % 10
            subsorteos_count = len(numeros_por_subsorteo)
            matriz[fila, col] = frecuencias.get(num, 0) / subsorteos_count * 100  # Porcentaje
    
    # Crear figura
    plt.figure(figsize=(14, 7))
    
    # Mapa de calor
    ax = sns.heatmap(
        matriz,
        annot=False,
        fmt='.1f',
        cmap='YlOrRd',
        cbar_kws={'label': 'Frecuencia (%)'},
        linewidths=0.5,
        linecolor='gray'
    )
    
    # Añadir números en cada celda
    for fila in range(5):
        for col in range(10):
            num = fila * 10 + col
            if num <= 45:
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
                    fontsize=12,
                    fontweight='bold',
                    color=color
                )
                ax.text(
                    col + 0.5,
                    fila + 0.7,
                    f'{freq_count}',
                    ha='center',
                    va='center',
                    fontsize=8,
                    color=color
                )
    
    plt.title(f'Mapa de Calor - Quini 6 (Todas las modalidades)\n(Frecuencia de aparición en {sorteos_count} sorteos = {len(numeros_por_subsorteo)} sub-sorteos)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('')
    plt.ylabel('')
    plt.xticks([])
    plt.yticks([])
    
    plt.tight_layout()
    return plt.gcf()


def crear_grafico_omision(numeros_por_subsorteo):
    """Crea un gráfico de barras de omisión."""
    # Calcular omisión
    ultimas_apariciones = {n: None for n in range(0, 46)}
    
    for idx, nums in enumerate(reversed(numeros_por_subsorteo)):
        for n in nums:
            if ultimas_apariciones[n] is None:
                ultimas_apariciones[n] = idx
    
    for n in ultimas_apariciones:
        if ultimas_apariciones[n] is None:
            ultimas_apariciones[n] = len(numeros_por_subsorteo)
    
    # Filtrar solo los que tienen omisión > 0 y ordenar
    omision_filtrada = {k: v for k, v in ultimas_apariciones.items() if v > 0}
    omision_ordenada = sorted(omision_filtrada.items(), key=lambda x: x[1], reverse=True)
    
    if not omision_ordenada:
        omision_ordenada = [(0, 0)]  # Placeholder
    
    # Tomar solo los top 20
    omision_top = omision_ordenada[:20]
    
    numeros = [f'{n:02d}' for n, _ in omision_top]
    valores = [v for _, v in omision_top]
    
    # Crear gráfico
    plt.figure(figsize=(14, 6))
    
    colors = sns.color_palette("Reds_r", len(numeros))
    bars = plt.bar(numeros, valores, color=colors, edgecolor='black', linewidth=0.5)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width()/2.,
            height,
            f'{int(height)}',
            ha='center',
            va='bottom',
            fontsize=10,
            fontweight='bold'
        )
    
    plt.title(f'Top 20 Números con Mayor Omisión - Quini 6\n(Sub-sorteos sin aparecer)', 
              fontsize=16, fontweight='bold', pad=20)
    plt.xlabel('Número', fontsize=12, fontweight='bold')
    plt.ylabel('Sub-sorteos sin aparecer', fontsize=12, fontweight='bold')
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    return plt.gcf()


def crear_visualizaciones():
    """Crea todas las visualizaciones y las guarda."""
    print("📊 Generando visualizaciones de Quini 6...\n")
    
    # Crear directorio de salida
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Cargar datos
    sorteos, numeros_por_subsorteo = cargar_datos()
    sorteos_count = len(sorteos)
    
    print(f"Sorteos cargados: {sorteos_count}")
    print(f"Sub-sorteos totales: {len(numeros_por_subsorteo)} (4 por sorteo)\n")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("Generando visualizaciones consolidadas...")
    
    # Mapa de calor de frecuencias
    fig_freq = crear_mapa_calor_frecuencias(numeros_por_subsorteo, sorteos_count)
    filename_freq = f"{OUTPUT_DIR}/quini6_mapa_calor_{timestamp}.png"
    fig_freq.savefig(filename_freq, dpi=300, bbox_inches='tight')
    print(f"  ✅ {filename_freq}")
    plt.close(fig_freq)
    
    # Gráfico de omisión
    fig_omision = crear_grafico_omision(numeros_por_subsorteo)
    filename_omision = f"{OUTPUT_DIR}/quini6_omision_{timestamp}.png"
    fig_omision.savefig(filename_omision, dpi=300, bbox_inches='tight')
    print(f"  ✅ {filename_omision}")
    plt.close(fig_omision)
    
    print(f"\n🎉 Visualizaciones guardadas en '{OUTPUT_DIR}/'")
    print(f"   Total: 2 imágenes generadas")


if __name__ == "__main__":
    crear_visualizaciones()
