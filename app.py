"""
Flask Backend for eCourts Scraper
Modern API with real-time updates and analytics
"""

from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import os
import json
from datetime import datetime
import threading
from ecourts_scraper import AdvancedECourtsScraper
import logging

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global scraper instance
scraper = None
scraper_lock = threading.Lock()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_scraper():
    """Get or create scraper instance"""
    global scraper
    with scraper_lock:
        if scraper is None:
            scraper = AdvancedECourtsScraper(headless=True)
    return scraper

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    })

@app.route('/api/states', methods=['GET'])
def get_states():
    """Get list of all states"""
    try:
        scraper_instance = get_scraper()
        states = scraper_instance.get_states()
        return jsonify({
            'success': True,
            'data': states,
            'count': len(states)
        })
    except Exception as e:
        logger.error(f"Error fetching states: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/districts', methods=['POST'])
def get_districts():
    """Get districts for a state"""
    try:
        data = request.json
        state_code = data.get('state_code')
        
        if not state_code:
            return jsonify({
                'success': False,
                'error': 'state_code is required'
            }), 400
        
        scraper_instance = get_scraper()
        districts = scraper_instance.get_districts(state_code)
        
        return jsonify({
            'success': True,
            'data': districts,
            'count': len(districts)
        })
    except Exception as e:
        logger.error(f"Error fetching districts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/complexes', methods=['POST'])
def get_complexes():
    """Get court complexes for a district"""
    try:
        data = request.json
        state_code = data.get('state_code')
        district_code = data.get('district_code')
        
        if not state_code or not district_code:
            return jsonify({
                'success': False,
                'error': 'state_code and district_code are required'
            }), 400
        
        scraper_instance = get_scraper()
        complexes = scraper_instance.get_court_complexes(state_code, district_code)
        
        return jsonify({
            'success': True,
            'data': complexes,
            'count': len(complexes)
        })
    except Exception as e:
        logger.error(f"Error fetching complexes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/courts', methods=['POST'])
def get_courts():
    """Get courts for a complex"""
    try:
        data = request.json
        complex_code = data.get('complex_code')
        
        if not complex_code:
            return jsonify({
                'success': False,
                'error': 'complex_code is required'
            }), 400
        
        scraper_instance = get_scraper()
        courts = scraper_instance.get_courts(complex_code)
        
        return jsonify({
            'success': True,
            'data': courts,
            'count': len(courts)
        })
    except Exception as e:
        logger.error(f"Error fetching courts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-cause-list', methods=['POST'])
def download_cause_list():
    """Download cause list for a single court"""
    try:
        data = request.json
        required_fields = ['state_code', 'district_code', 'complex_code', 
                          'court_code', 'date']
        
        # Validate required fields
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        scraper_instance = get_scraper()
        result = scraper_instance.download_cause_list(
            state_code=data['state_code'],
            district_code=data['district_code'],
            complex_code=data['complex_code'],
            court_code=data['court_code'],
            date_str=data['date'],
            court_name=data.get('court_name', '')
        )
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error downloading cause list: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-all-cause-lists', methods=['POST'])
def download_all_cause_lists():
    """Download cause lists for all courts in a complex"""
    try:
        data = request.json
        required_fields = ['state_code', 'district_code', 'complex_code', 'date']
        
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'{field} is required'
                }), 400
        
        # Start background task
        def download_task():
            scraper_instance = get_scraper()
            results = scraper_instance.download_all_courts_cause_lists(
                state_code=data['state_code'],
                district_code=data['district_code'],
                complex_code=data['complex_code'],
                date_str=data['date']
            )
            
            # Emit completion via WebSocket
            socketio.emit('download_complete', {
                'results': results,
                'timestamp': datetime.now().isoformat()
            })
        
        thread = threading.Thread(target=download_task)
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Bulk download started. You will be notified when complete.'
        })
    except Exception as e:
        logger.error(f"Error in bulk download: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/files')
def list_files():
    """List all downloaded files"""
    try:
        pdfs = []
        if os.path.exists('pdfs'):
            pdfs = [
                {
                    'name': f,
                    'size': os.path.getsize(os.path.join('pdfs', f)),
                    'modified': os.path.getmtime(os.path.join('pdfs', f))
                }
                for f in os.listdir('pdfs') if f.endswith('.pdf')
            ]
        
        results = []
        if os.path.exists('results'):
            results = [
                {
                    'name': f,
                    'size': os.path.getsize(os.path.join('results', f)),
                    'modified': os.path.getmtime(os.path.join('results', f))
                }
                for f in os.listdir('results') if f.endswith('.json')
            ]
        
        return jsonify({
            'success': True,
            'pdfs': pdfs,
            'results': results,
            'total': len(pdfs) + len(results)
        })
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/download-file/<path:filename>')
def download_file(filename):
    """Download a specific file"""
    try:
        if filename.endswith('.pdf'):
            directory = 'pdfs'
        elif filename.endswith('.json'):
            directory = 'results'
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        filepath = os.path.join(directory, filename)
        
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics')
def get_analytics():
    """Get scraper analytics"""
    try:
        scraper_instance = get_scraper()
        analytics = scraper_instance.get_analytics()
        
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/view-json/<filename>')
def view_json(filename):
    """View JSON file contents"""
    try:
        filepath = os.path.join('results', filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        logger.error(f"Error viewing JSON: {e}")
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connection_response', {'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('downloads', exist_ok=True)
    os.makedirs('results', exist_ok=True)
    os.makedirs('pdfs', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    logger.info("Starting eCourts Scraper API Server...")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
