# app.py - Flask Web Application for Tombola Analytics
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
import json
from datetime import datetime

# Import existing modules
from tombola.telekino import procesar_estadisticas as telekino_stats
from tombola.quini6 import procesar_estadisticas as quini6_stats
from tombola.quini6_verificar import verificar_jugadas
from tombola import telekino_scraper, quini6_scraper
from tombola.stats_cache import load_cached_stats
import config
from auth import require_api_key

app = Flask(__name__)
CORS(app)

# Configuration
VISUALIZACIONES_DIR = config.VISUALIZACIONES_DIR
DATA_DIR = config.DATA_DIR

# ==================== ROUTES - PAGES ====================

@app.route('/')
def index():
    """Dashboard principal."""
    return render_template('index.html')

@app.route('/telekino')
def telekino_page():
    """Página de estadísticas Telekino."""
    return render_template('telekino.html')

@app.route('/quini6')
def quini6_page():
    """Página de estadísticas Quini 6."""
    return render_template('quini6.html')

# ==================== API ENDPOINTS - TELEKINO ====================

@app.route('/api/telekino/stats', methods=['GET'])
def api_telekino_stats():
    """
    Get Telekino statistics.
    Query params:
        - fecha: YYYY-MM-DD (optional) - filter stats up to this date
    """
    try:
        fecha_limite = request.args.get('fecha', None)
        
        # Try to load from cache
        cached = load_cached_stats('telekino', fecha_limite)
        if cached:
            return jsonify({
                'success': True,
                'cached': True,
                'data': cached['stats']
            })
        
        # Calculate stats (this will also cache them)
        # We need to capture the output, so we'll call the functions directly
        from tombola.telekino import load_data, calcular_frecuencias, calcular_omision, calcular_coocurrencia, calcular_demora_maxima
        
        sorteos, numeros_por_sorteo = load_data(fecha_limite)
        frec = calcular_frecuencias(numeros_por_sorteo)
        omision = calcular_omision(sorteos, numeros_por_sorteo)
        cooc = calcular_coocurrencia(numeros_por_sorteo)
        demora_max = calcular_demora_maxima(sorteos, numeros_por_sorteo)
        
        stats_data = {
            'sorteos_count': len(sorteos),
            'frecuencias': dict(frec.most_common()),
            'omision': omision,
            'coocurrencia': {f"{a}-{b}": v for (a, b), v in cooc.most_common()},
            'demora_maxima': demora_max
        }
        
        # Save to cache
        from tombola.stats_cache import save_stats_to_cache
        save_stats_to_cache('telekino', fecha_limite, stats_data)
        
        return jsonify({
            'success': True,
            'cached': False,
            'data': stats_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/telekino/scrape', methods=['POST'])
@require_api_key
def api_telekino_scrape():
    """Scrape Telekino draw using the same logic as main.py."""
    try:
        # Get all saved dates
        saved_dates = telekino_scraper.get_all_saved_sorteos()
        
        # Get last Sunday available
        last_sunday = telekino_scraper.get_last_sunday()
        
        # If it's today, go back one week (today's draw isn't available yet)
        if last_sunday == datetime.now().date():
            last_sunday = telekino_scraper.previous_telekino_date(last_sunday)
        
        # Get last saved sorteo
        last_saved = telekino_scraper.get_last_saved_sorteo()
        
        if last_saved:
            next_date = telekino_scraper.next_telekino_date(last_saved["fecha"])
            
            # Check if we're already up-to-date going forward
            if next_date > last_sunday:
                # We're up-to-date, search backwards for older sorteos
                first_saved = telekino_scraper.get_first_saved_sorteo()
                if first_saved:
                    prev_date = telekino_scraper.previous_telekino_date(first_saved["fecha"])
                    
                    # Check if already saved
                    if prev_date in saved_dates:
                        return jsonify({
                            'success': True,
                            'message': f'Already up-to-date. Sorteo {prev_date} already exists.',
                            'direction': 'backward'
                        })
                    
                    # Fetch previous sorteo
                    result = telekino_scraper.fetch_sorteo(prev_date)
                    if result:
                        telekino_scraper.save_to_csv(result)
                        return jsonify({
                            'success': True,
                            'message': f'Historical sorteo {result["sorteo"]} ({prev_date}) saved successfully',
                            'sorteo': result["sorteo"],
                            'fecha': prev_date.strftime('%Y-%m-%d'),
                            'direction': 'backward'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'Sorteo for {prev_date} not found - may not be available on the web',
                            'direction': 'backward'
                        })
                
                return jsonify({
                    'success': True,
                    'message': 'Already up-to-date and no older sorteos to fetch'
                })
            
            # Check if next sorteo is already saved
            if next_date in saved_dates:
                return jsonify({
                    'success': True,
                    'message': f'Sorteo for {next_date} already saved',
                    'direction': 'forward'
                })
            
            # Fetch next sorteo (forward)
            result = telekino_scraper.fetch_sorteo(next_date)
        else:
            # No CSV yet, fetch the most recent sorteo available
            next_date = last_sunday
            result = telekino_scraper.fetch_sorteo(next_date)
        
        if result:
            telekino_scraper.save_to_csv(result)
            return jsonify({
                'success': True,
                'message': f'Sorteo {result["sorteo"]} ({next_date}) saved successfully',
                'sorteo': result["sorteo"],
                'fecha': next_date.strftime('%Y-%m-%d') if hasattr(next_date, 'strftime') else str(next_date),
                'direction': 'forward'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Sorteo for {next_date} not found - may not be published yet'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/telekino/sorteos', methods=['GET'])
def api_telekino_sorteos():
    """Get paginated Telekino sorteos with optional date filter."""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))  # Changed to 10
        fecha_filtro = request.args.get('fecha', None)
        
        # Load all sorteos
        import csv
        sorteos = []
        with open(f'{config.DATA_DIR}/telekino.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('sorteo'):
                    continue
                sorteo_data = {
                    'sorteo': row['sorteo'],
                    'fecha': row['fecha'],
                    'numeros': [int(row[f'n{i}']) for i in range(1, 16)]
                }
                sorteos.append(sorteo_data)
        
        # Sort by date ASCENDING (oldest to newest)
        sorteos.sort(key=lambda x: x['fecha'])
        
        # If filtered by date, find that sorteo and show it as FIRST with next 9
        filtered_index = None
        if fecha_filtro:
            for idx, sorteo in enumerate(sorteos):
                if sorteo['fecha'] == fecha_filtro:
                    # Calculate page where this sorteo would be the FIRST one
                    page = (idx // per_page) + 1
                    # Start from this sorteo
                    start = idx
                    end = start + per_page
                    filtered_index = 0  # Always first in the page
                    
                    sorteos_page = sorteos[start:end]
                    total = len(sorteos)
                    total_pages = (total + per_page - 1) // per_page
                    
                    return jsonify({
                        'success': True,
                        'sorteos': sorteos_page,
                        'pagination': {
                            'page': page,
                            'per_page': per_page,
                            'total': total,
                            'total_pages': total_pages,
                            'has_prev': idx > 0,
                            'has_next': end < total
                        },
                        'filtered_sorteo_index': filtered_index
                    })
            
            # If fecha not found, return error
            return jsonify({
                'success': False,
                'error': f'No se encontró sorteo para la fecha {fecha_filtro}'
            }), 404
        
        # Normal pagination (no filter)
        total = len(sorteos)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        sorteos_page = sorteos[start:end]
        
        return jsonify({
            'success': True,
            'sorteos': sorteos_page,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            },
            'filtered_sorteo_index': None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== API ENDPOINTS - QUINI 6 ====================

@app.route('/api/quini6/stats', methods=['GET'])
def api_quini6_stats():
    """
    Get Quini 6 statistics.
    Query params:
        - fecha: YYYY-MM-DD (optional) - filter stats up to this date
    """
    try:
        fecha_limite = request.args.get('fecha', None)
        
        # Try to load from cache
        cached = load_cached_stats('quini6', fecha_limite)
        if cached:
            return jsonify({
                'success': True,
                'cached': True,
                'data': cached['stats']
            })
        
        # Calculate stats
        from tombola.quini6 import load_data, calcular_frecuencias, calcular_omision, calcular_coocurrencia, calcular_demora_maxima
        
        sorteos, numeros_por_sorteo = load_data(fecha_limite)
        frec = calcular_frecuencias(numeros_por_sorteo)
        omision = calcular_omision(numeros_por_sorteo)
        cooc = calcular_coocurrencia(numeros_por_sorteo)
        demora_max = calcular_demora_maxima(numeros_por_sorteo)
        
        stats_data = {
            'sorteos_count': len(sorteos),
            'subsorteos_count': len(numeros_por_sorteo),
            'frecuencias': dict(frec.most_common()),
            'omision': omision,
            'coocurrencia': {f"{a}-{b}": v for (a, b), v in cooc.most_common()},
            'demora_maxima': demora_max
        }
        
        # Save to cache
        from tombola.stats_cache import save_stats_to_cache
        save_stats_to_cache('quini6', fecha_limite, stats_data)
        
        return jsonify({
            'success': True,
            'cached': False,
            'data': stats_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quini6/scrape', methods=['POST'])
@require_api_key
def api_quini6_scrape():
    """Scrape Quini 6 draw using the same logic as main.py."""
    try:
        saved_dates = quini6_scraper.get_all_saved_sorteos()
        last_quini6_date = quini6_scraper.get_last_quini6_date()
        
        # If it's today, may not be published yet
        if last_quini6_date == datetime.now().date():
            last_quini6_date = quini6_scraper.previous_quini6_date(last_quini6_date)
        
        last_saved = quini6_scraper.get_last_saved_sorteo()
        
        if last_saved:
            next_date = quini6_scraper.next_quini6_date(last_saved["fecha"])
            
            # Check if we're already up-to-date
            if next_date > last_quini6_date:
                # We're up-to-date, search backwards for older sorteos
                first_saved = quini6_scraper.get_first_saved_sorteo()
                if first_saved:
                    prev_date = quini6_scraper.previous_quini6_date(first_saved["fecha"])
                    
                    # Check if it's excluded
                    if quini6_scraper.is_fecha_excluida(prev_date):
                        # Try the previous date
                        prev_date = quini6_scraper.previous_quini6_date(prev_date)
                    
                    # Check if already saved
                    if prev_date in saved_dates:
                        return jsonify({
                            'success': True,
                            'message': f'Already up-to-date. Sorteo {prev_date} already exists.',
                            'direction': 'backward'
                        })
                    
                    # Fetch previous sorteo
                    result = quini6_scraper.fetch_sorteo(prev_date)
                    if result:
                        quini6_scraper.save_to_csv(result)
                        return jsonify({
                            'success': True,
                            'message': f'Historical sorteo {result["sorteo"]} ({prev_date}) saved successfully',
                            'sorteo': result["sorteo"],
                            'fecha': prev_date.strftime('%Y-%m-%d'),
                            'direction': 'backward'
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'message': f'Sorteo for {prev_date} not found - may be a holiday or not published',
                            'direction': 'backward',
                            'fecha': prev_date.strftime('%Y-%m-%d')
                        })
                
                return jsonify({
                    'success': True,
                    'message': 'Already up-to-date and no older sorteos to fetch'
                })
            
            # Check if next sorteo is already saved
            if next_date in saved_dates:
                return jsonify({
                    'success': True,
                    'message': f'Sorteo for {next_date} already saved',
                    'direction': 'forward'
                })
            
            # Fetch next sorteo (forward)
            result = quini6_scraper.fetch_sorteo(next_date)
        else:
            # No CSV yet, fetch the most recent sorteo available
            next_date = last_quini6_date
            result = quini6_scraper.fetch_sorteo(next_date)
        
        if result:
            quini6_scraper.save_to_csv(result)
            return jsonify({
                'success': True,
                'message': f'Sorteo {result["sorteo"]} ({next_date}) saved successfully',
                'sorteo': result["sorteo"],
                'fecha': next_date.strftime('%Y-%m-%d') if hasattr(next_date, 'strftime') else str(next_date),
                'direction': 'forward'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Sorteo for {next_date} not found - may not be published yet'
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quini6/verificar', methods=['GET'])
def api_quini6_verificar():
    """Verify Quini 6 plays against latest draw."""
    try:
        from tombola.quini6_verificar import cargar_mis_jugadas, cargar_ultimo_sorteo, contar_aciertos
        
        jugadas = cargar_mis_jugadas()
        sorteo = cargar_ultimo_sorteo()
        
        if not sorteo:
            return jsonify({
                'success': False,
                'error': 'No hay sorteos guardados'
            }), 404
        
        modalidades = [
            ('tradicional', sorteo['tradicional']),
            ('segunda', sorteo['segunda']),
            ('revancha', sorteo['revancha']),
            ('siempre_sale', sorteo['siempre_sale'])
        ]
        
        resultados = {}
        for modalidad_key, numeros_sorteo in modalidades:
            ganadores = []
            for jugada in jugadas:
                cantidad_aciertos, numeros_acertados = contar_aciertos(
                    jugada['numeros'],
                    numeros_sorteo
                )
                if cantidad_aciertos >= 3:
                    ganadores.append({
                        'id': jugada['id'],
                        'aciertos': cantidad_aciertos,
                        'numeros_acertados': numeros_acertados,
                        'jugada': jugada['numeros']
                    })
            
            resultados[modalidad_key] = {
                'numeros_sorteo': numeros_sorteo,
                'ganadores': ganadores
            }
        
        return jsonify({
            'success': True,
            'sorteo': {
                'numero': sorteo['sorteo'],
                'fecha': sorteo['fecha']
            },
            'resultados': resultados
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== HEATMAP ENDPOINTS ====================


@app.route('/api/quini6/sorteos', methods=['GET'])
def api_quini6_sorteos():
    """Get paginated Quini6 sorteos."""
    try:
        page = int(request.args.get('page', 1))
        per_page = 3
        fecha_filtro = request.args.get('fecha', None)
        
        import csv
        sorteos = []
        with open(f'{config.DATA_DIR}/quini6.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('sorteo'):
                    continue
                sorteos.append({
                    'sorteo': row['sorteo'],
                    'fecha': row['fecha'],
                    'tradicional': [int(row[f't{i}']) for i in range(1, 7)],
                    'segunda': [int(row[f's{i}']) for i in range(1, 7)],
                    'revancha': [int(row[f'r{i}']) for i in range(1, 7)],
                    'siempre_sale': [int(row[f'ss{i}']) for i in range(1, 7)]
                })
        
        sorteos.sort(key=lambda x: x['fecha'])
        
        if fecha_filtro:
            for idx, sorteo in enumerate(sorteos):
                if sorteo['fecha'] == fecha_filtro:
                    start = idx
                    end = start + per_page
                    total = len(sorteos)
                    return jsonify({
                        'success': True,
                        'sorteos': sorteos[start:end],
                        'pagination': {
                            'page': (idx // per_page) + 1,
                            'per_page': per_page,
                            'total': total,
                            'total_pages': (total + per_page - 1) // per_page,
                            'has_prev': idx > 0,
                            'has_next': end < total
                        },
                        'filtered_sorteo_index': 0
                    })
            return jsonify({'success': False, 'error': f'Fecha {fecha_filtro} no encontrada'}), 404
        
        total = len(sorteos)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page
        
        return jsonify({
            'success': True,
            'sorteos': sorteos[start:end],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_prev': page > 1,
                'has_next': page < total_pages
            },
            'filtered_sorteo_index': None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/telekino/heatmap', methods=['GET'])
def api_telekino_heatmap():
    """Generate Telekino heatmap image."""
    try:
        fecha_limite = request.args.get('fecha', None)
        
        # Try to load from cache
        from tombola.heatmap_cache import load_cached_heatmap, save_heatmap_to_cache
        
        cached_file = load_cached_heatmap('telekino', fecha_limite)
        if cached_file:
            from flask import send_file
            return send_file(cached_file, mimetype='image/png', as_attachment=False)
        
        # Generate new heatmap
        import matplotlib
        matplotlib.use('Agg')  # Non-GUI backend
        from analysis.visualizacion_telekino import cargar_datos, crear_mapa_calor_frecuencias
        
        sorteos, numeros_por_sorteo = cargar_datos(fecha_limite)
        fig = crear_mapa_calor_frecuencias(numeros_por_sorteo, len(sorteos))
        
        # Save to cache
        heatmap_file = save_heatmap_to_cache('telekino', fecha_limite, fig)
        
        import matplotlib.pyplot as plt
        plt.close(fig)
        
        from flask import send_file
        return send_file(heatmap_file, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/quini6/heatmap', methods=['GET'])
def api_quini6_heatmap():
    """Generate Quini 6 heatmap image."""
    try:
        fecha_limite = request.args.get('fecha', None)
        
        # Try to load from cache
        from tombola.heatmap_cache import load_cached_heatmap, save_heatmap_to_cache
        
        cached_file = load_cached_heatmap('quini6', fecha_limite)
        if cached_file:
            from flask import send_file
            return send_file(cached_file, mimetype='image/png', as_attachment=False)
        
        # Generate new heatmap
        import matplotlib
        matplotlib.use('Agg')  # Non-GUI backend
        from analysis.visualizacion_quini6 import cargar_datos, crear_mapa_calor_frecuencias
        
        sorteos, numeros_por_subsorteo = cargar_datos(fecha_limite)
        fig = crear_mapa_calor_frecuencias(numeros_por_subsorteo, len(sorteos))
        
        # Save to cache
        heatmap_file = save_heatmap_to_cache('quini6', fecha_limite, fig)
        
        import matplotlib.pyplot as plt
        plt.close(fig)
        
        from flask import send_file
        return send_file(heatmap_file, mimetype='image/png', as_attachment=False)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ==================== STATIC FILES ====================

@app.route('/visualizaciones/<path:filename>')
def serve_visualization(filename):
    """Serve visualization images."""
    return send_from_directory(VISUALIZACIONES_DIR, filename)

@app.route('/api/cache/clear', methods=['POST'])
@require_api_key
def api_clear_cache():
    """Clear all cached stats and visualizations to force regeneration."""
    try:
        import glob
        
        deleted_files = {
            'stats_cache': [],
            'visualizaciones': []
        }
        
        # Clear stats cache
        stats_cache_pattern = os.path.join(config.STATS_CACHE_DIR, '*.json')
        for file_path in glob.glob(stats_cache_pattern):
            try:
                os.remove(file_path)
                deleted_files['stats_cache'].append(os.path.basename(file_path))
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        # Clear visualizations
        viz_pattern = os.path.join(config.VISUALIZACIONES_DIR, '*.png')
        for file_path in glob.glob(viz_pattern):
            try:
                os.remove(file_path)
                deleted_files['visualizaciones'].append(os.path.basename(file_path))
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")
        
        return jsonify({
            'success': True,
            'message': 'Cache cleared successfully',
            'deleted': {
                'stats_cache': len(deleted_files['stats_cache']),
                'visualizaciones': len(deleted_files['visualizaciones'])
            },
            'files': deleted_files
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# ==================== RUN ====================

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    os.makedirs(config.STATS_CACHE_DIR, exist_ok=True)
    os.makedirs(config.VISUALIZACIONES_DIR, exist_ok=True)
    
    print("✅ App starting - automated scraping handled by GitHub Actions")
    print("   • Telekino: Mondays at 5:00 AM")
    print("   • Quini6: Mondays and Thursdays at 5:00 AM")
    
    # Run development server
    app.run(host='0.0.0.0', port=8080, debug=True)

