"""
Web Server Module
Flask application with REST API and WebSocket support
Provides web interface for motor control system
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from functools import wraps

from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit

from .execution_manager import ExecutionManager

logger = logging.getLogger(__name__)


class WebServer:
    """Flask web server with SocketIO for real-time updates"""
    
    def __init__(self, execution_manager: ExecutionManager, config: Dict[str, Any], gpio_monitor=None):
        """
        Initialize web server
        
        Args:
            execution_manager: Execution manager instance
            config: Web server configuration
            gpio_monitor: GPIO monitor instance (optional)
        """
        self.execution_manager = execution_manager
        self.config = config
        self.gpio_monitor = gpio_monitor
        
        # Create Flask app
        template_dir = Path(__file__).parent.parent / 'templates'
        static_dir = Path(__file__).parent.parent / 'static'
        
        self.app = Flask(__name__,
                        template_folder=str(template_dir),
                        static_folder=str(static_dir))
        
        self.app.secret_key = config.get('secret_key', 'change-this-secret-key')
        
        # Create SocketIO instance with threading mode (simple, no async deps)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Set status callback
        self.execution_manager.status_callback = self._broadcast_status
        
        # Register routes
        self._register_routes()
        self._register_socketio_events()
        
        logger.info("Web server initialized")
    
    def _require_auth(self, f):
        """Decorator for engineer menu authentication"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if authenticated
            if not session.get('engineer_authenticated'):
                return jsonify({'error': 'Authentication required'}), 401
            return f(*args, **kwargs)
        return decorated_function
    
    def _register_routes(self):
        """Register Flask routes"""
        
        # Main page
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # Engineer menu page
        @self.app.route('/engineer')
        def engineer():
            if not session.get('engineer_authenticated'):
                return render_template('engineer_login.html')
            return render_template('engineer.html')
        
        # Logs page
        @self.app.route('/logs')
        def logs():
            return render_template('logs.html')
        
        # GPIO Monitor page
        @self.app.route('/gpio')
        def gpio_monitor_page():
            return render_template('gpio_monitor.html')
        
        # API: Get system status
        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            try:
                status = self.execution_manager.get_status()
                return jsonify(status)
            except Exception as e:
                logger.error(f"Status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Select logic (A or B)
        @self.app.route('/api/select_logic', methods=['POST'])
        def select_logic():
            try:
                data = request.get_json()
                logic = data.get('logic', '').upper()
                
                if logic not in ['A', 'B']:
                    return jsonify({'error': 'Invalid logic (must be A or B)'}), 400
                
                success = self.execution_manager.select_logic(logic)
                
                if success:
                    return jsonify({'success': True, 'message': f'Logic {logic} selected'})
                else:
                    return jsonify({'error': 'Failed to select logic'}), 400
            except Exception as e:
                logger.error(f"Select logic error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Select mode (1-5)
        @self.app.route('/api/select_mode', methods=['POST'])
        def select_mode():
            try:
                data = request.get_json()
                mode = int(data.get('mode', 0))
                
                if mode < 1 or mode > 5:
                    return jsonify({'error': 'Invalid mode (must be 1-5)'}), 400
                
                success = self.execution_manager.select_mode(mode)
                
                if success:
                    return jsonify({'success': True, 'message': f'Mode {mode} selected'})
                else:
                    return jsonify({'error': 'Failed to select mode'}), 400
            except Exception as e:
                logger.error(f"Select mode error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Start execution
        @self.app.route('/api/start', methods=['POST'])
        def start_execution():
            """Start the logic thread (initializes the system)"""
            try:
                success = self.execution_manager.start_selected_logic()
                
                if success:
                    return jsonify({'success': True, 'message': 'Logic thread started'})
                else:
                    return jsonify({'error': 'Failed to start logic thread'}), 400
            except Exception as e:
                logger.error(f"Start error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Simulate button press (for web interface control)
        @self.app.route('/api/button/<button_name>', methods=['POST'])
        def press_button(button_name):
            """Simulate a physical button press"""
            try:
                # Valid button names: start, stop, reset, tala
                valid_buttons = ['start', 'stop', 'reset', 'tala']
                if button_name not in valid_buttons:
                    return jsonify({'error': f'Invalid button name. Valid: {valid_buttons}'}), 400
                
                # Simulate button press and release
                hw = self.execution_manager.hw
                hw.simulate_button_press(button_name)
                # Auto-release after 100ms
                import time, threading
                def release_button():
                    time.sleep(0.1)
                    hw.simulate_button_release(button_name)
                threading.Thread(target=release_button, daemon=True).start()
                
                return jsonify({'success': True, 'message': f'{button_name.capitalize()} button pressed'})
            except Exception as e:
                logger.error(f"Button press error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Stop execution
        @self.app.route('/api/stop', methods=['POST'])
        def stop_execution():
            """Stop the logic thread"""
            try:
                success = self.execution_manager.stop_active_logic()
                
                if success:
                    return jsonify({'success': True, 'message': 'Execution stopped'})
                else:
                    return jsonify({'error': 'No active execution'}), 400
            except Exception as e:
                logger.error(f"Stop error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Emergency stop
        @self.app.route('/api/emergency_stop', methods=['POST'])
        def emergency_stop():
            try:
                self.execution_manager.emergency_stop_all()
                return jsonify({'success': True, 'message': 'Emergency stop executed'})
            except Exception as e:
                logger.error(f"Emergency stop error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Enable manual mode
        @self.app.route('/api/manual/enable', methods=['POST'])
        def enable_manual():
            try:
                success = self.execution_manager.enable_manual_mode()
                
                if success:
                    return jsonify({'success': True, 'message': 'Manual mode enabled'})
                else:
                    return jsonify({'error': 'Failed to enable manual mode'}), 400
            except Exception as e:
                logger.error(f"Manual enable error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Disable manual mode
        @self.app.route('/api/manual/disable', methods=['POST'])
        def disable_manual():
            try:
                success = self.execution_manager.disable_manual_mode()
                
                if success:
                    return jsonify({'success': True, 'message': 'Manual mode disabled'})
                else:
                    return jsonify({'error': 'Failed to disable manual mode'}), 400
            except Exception as e:
                logger.error(f"Manual disable error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Engineer login
        @self.app.route('/api/engineer/login', methods=['POST'])
        def engineer_login():
            try:
                data = request.get_json()
                password = data.get('password', '')
                
                if password == self.config.get('engineer_password', '1234'):
                    session['engineer_authenticated'] = True
                    return jsonify({'success': True, 'message': 'Authentication successful'})
                else:
                    return jsonify({'error': 'Invalid password'}), 401
            except Exception as e:
                logger.error(f"Login error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Engineer logout
        @self.app.route('/api/engineer/logout', methods=['POST'])
        def engineer_logout():
            session.pop('engineer_authenticated', None)
            return jsonify({'success': True, 'message': 'Logged out'})
        
        # API: Get configuration
        @self.app.route('/api/config/<logic>', methods=['GET'])
        @self._require_auth
        def get_config(logic):
            try:
                config = self.execution_manager.get_configuration(logic.upper())
                
                if config:
                    return jsonify(config)
                else:
                    return jsonify({'error': 'Invalid logic'}), 400
            except Exception as e:
                logger.error(f"Get config error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Update parameter
        @self.app.route('/api/config/update', methods=['POST'])
        @self._require_auth
        def update_parameter():
            try:
                data = request.get_json()
                logic = data.get('logic', '').upper()
                parameter = data.get('parameter', '')
                value = data.get('value')
                
                if not logic or not parameter:
                    return jsonify({'error': 'Missing logic or parameter'}), 400
                
                success = self.execution_manager.update_parameter(logic, parameter, value)
                
                if success:
                    return jsonify({'success': True, 'message': 'Parameter updated'})
                else:
                    return jsonify({'error': 'Failed to update parameter'}), 400
            except Exception as e:
                logger.error(f"Update parameter error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Get all pins status
        @self.app.route('/api/gpio/status', methods=['GET'])
        def get_gpio_status():
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                pins = self.gpio_monitor.get_all_pins_status()
                return jsonify({'pins': pins})
            except Exception as e:
                logger.error(f"GPIO status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Get pin groups
        @self.app.route('/api/gpio/groups', methods=['GET'])
        def get_gpio_groups():
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                groups = self.gpio_monitor.get_pin_groups()
                return jsonify(groups)
            except Exception as e:
                logger.error(f"GPIO groups error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Get specific pin status
        @self.app.route('/api/gpio/pin/<int:pin>', methods=['GET'])
        def get_pin_status(pin):
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                status = self.gpio_monitor.get_pin_status(pin)
                if status:
                    return jsonify(status)
                else:
                    return jsonify({'error': 'Pin not found'}), 404
            except Exception as e:
                logger.error(f"Pin status error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Write to pin
        @self.app.route('/api/gpio/write', methods=['POST'])
        def write_gpio_pin():
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                data = request.get_json()
                pin = data.get('pin')
                value = data.get('value')
                
                if pin is None or value is None:
                    return jsonify({'error': 'Missing pin or value'}), 400
                
                result = self.gpio_monitor.write_pin(int(pin), int(value))
                
                # Broadcast GPIO update via websocket
                if result.get('success'):
                    self.socketio.emit('gpio_update', {
                        'pin': pin,
                        'value': value,
                        'name': result.get('name', '')
                    })
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"GPIO write error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Simulate button press
        @self.app.route('/api/gpio/button_press', methods=['POST'])
        def simulate_button_press():
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                data = request.get_json()
                pin = data.get('pin')
                duration = data.get('duration', 100)
                
                if pin is None:
                    return jsonify({'error': 'Missing pin'}), 400
                
                result = self.gpio_monitor.simulate_button_press(int(pin), int(duration))
                
                # Broadcast button press via websocket
                if result.get('success'):
                    self.socketio.emit('button_pressed', {
                        'pin': pin,
                        'name': result.get('name', ''),
                        'duration': duration
                    })
                
                return jsonify(result)
            except Exception as e:
                logger.error(f"Button press simulation error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: GPIO Monitor - Get writable pins
        @self.app.route('/api/gpio/writable', methods=['GET'])
        def get_writable_pins():
            try:
                if not self.gpio_monitor:
                    return jsonify({'error': 'GPIO monitor not available'}), 503
                
                pins = self.gpio_monitor.get_input_pins()
                return jsonify({'pins': pins})
            except Exception as e:
                logger.error(f"Get writable pins error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Get configuration by type
        @self.app.route('/api/config/<config_type>', methods=['GET'])
        @self._require_auth
        def get_config_file(config_type):
            try:
                config_path = Path(__file__).parent.parent / 'config'
                
                if config_type == 'logic_a':
                    file_path = config_path / 'config_logic_a.json'
                elif config_type == 'logic_b':
                    file_path = config_path / 'config_logic_b.json'
                elif config_type == 'system':
                    file_path = config_path / 'system_config.json'
                else:
                    return jsonify({'error': 'Invalid config type'}), 400
                
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
                
                return jsonify({'success': True, 'config': config_data})
            except Exception as e:
                logger.error(f"Get config file error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Save configuration
        @self.app.route('/api/config/<config_type>', methods=['POST'])
        @self._require_auth
        def save_config_file(config_type):
            try:
                data = request.get_json()
                config_data = data.get('config')
                
                if not config_data:
                    return jsonify({'error': 'No configuration provided'}), 400
                
                config_path = Path(__file__).parent.parent / 'config'
                
                if config_type == 'logic_a':
                    file_path = config_path / 'config_logic_a.json'
                elif config_type == 'logic_b':
                    file_path = config_path / 'config_logic_b.json'
                elif config_type == 'system':
                    file_path = config_path / 'system_config.json'
                else:
                    return jsonify({'error': 'Invalid config type'}), 400
                
                # Backup current config
                backup_path = file_path.with_suffix('.json.bak')
                if file_path.exists():
                    import shutil
                    shutil.copy(file_path, backup_path)
                
                # Save new config
                with open(file_path, 'w') as f:
                    json.dump(config_data, f, indent=2)
                
                return jsonify({'success': True, 'message': 'Configuration saved'})
            except Exception as e:
                logger.error(f"Save config error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Reload configuration
        @self.app.route('/api/reload_config', methods=['POST'])
        def reload_config():
            try:
                # Stop the current logic if running
                if self.execution_manager.get_current_logic():
                    self.execution_manager.stop_logic()
                    time.sleep(0.5)  # Wait for clean stop
                
                # Reload the configuration by restarting the logic if one was selected
                selected_logic = self.execution_manager.current_logic
                if selected_logic:
                    # Re-select the same logic to reload config
                    self.execution_manager.select_logic(selected_logic)
                    logger.info(f"Reloaded configuration for {selected_logic}")
                
                return jsonify({'success': True, 'message': 'Configuration reloaded'})
            except Exception as e:
                logger.error(f"Reload config error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Get logs
        @self.app.route('/api/logs/<log_type>', methods=['GET'])
        def get_logs(log_type):
            try:
                lines = int(request.args.get('lines', 100))
                
                log_path = Path(__file__).parent.parent / 'logs'
                
                if log_type == 'operations':
                    log_file = log_path / 'operations.csv'
                elif log_type == 'parameters':
                    log_file = log_path / 'parameters.csv'
                elif log_type == 'errors':
                    log_file = log_path / 'errors.csv'
                else:
                    return jsonify({'error': 'Invalid log type'}), 400
                
                if not log_file.exists():
                    return jsonify({
                        'success': True,
                        'logs': [],
                        'headers': ['Timestamp', 'Event', 'Details'],
                        'stats': {'total_operations': 0, 'total_errors': 0, 'last_operation': 'None', 'log_size': '0 KB'}
                    })
                
                # Read log file
                import csv
                logs = []
                headers = []
                
                with open(log_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    headers = next(reader, [])
                    logs = list(reader)[-lines:]  # Get last N lines
                
                # Get stats
                stats = {
                    'total_operations': len(logs),
                    'total_errors': sum(1 for row in logs if 'error' in str(row).lower()),
                    'last_operation': logs[-1][0] if logs else 'None',
                    'log_size': f"{log_file.stat().st_size / 1024:.2f} KB"
                }
                
                return jsonify({
                    'success': True,
                    'logs': logs,
                    'headers': headers,
                    'stats': stats
                })
            except Exception as e:
                logger.error(f"Get logs error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Download log file
        @self.app.route('/api/logs/<log_type>/download', methods=['GET'])
        def download_log(log_type):
            try:
                from flask import send_file
                
                log_path = Path(__file__).parent.parent / 'logs'
                
                if log_type == 'operations':
                    log_file = log_path / 'operations.csv'
                elif log_type == 'parameters':
                    log_file = log_path / 'parameters.csv'
                elif log_type == 'errors':
                    log_file = log_path / 'errors.csv'
                else:
                    return jsonify({'error': 'Invalid log type'}), 400
                
                if log_file.exists():
                    return send_file(log_file, as_attachment=True, download_name=log_file.name)
                else:
                    return jsonify({'error': 'Log file not found'}), 404
            except Exception as e:
                logger.error(f"Download log error: {e}")
                return jsonify({'error': str(e)}), 500
        
        # API: Clear log file
        @self.app.route('/api/logs/<log_type>', methods=['DELETE'])
        def clear_log(log_type):
            try:
                log_path = Path(__file__).parent.parent / 'logs'
                
                if log_type == 'operations':
                    log_file = log_path / 'operations.csv'
                elif log_type == 'parameters':
                    log_file = log_path / 'parameters.csv'
                elif log_type == 'errors':
                    log_file = log_path / 'errors.csv'
                else:
                    return jsonify({'error': 'Invalid log type'}), 400
                
                if log_file.exists():
                    # Keep header, clear data
                    import csv
                    with open(log_file, 'r') as f:
                        reader = csv.reader(f)
                        headers = next(reader, [])
                    
                    with open(log_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(headers)
                    
                    return jsonify({'success': True, 'message': 'Log cleared'})
                else:
                    return jsonify({'error': 'Log file not found'}), 404
            except Exception as e:
                logger.error(f"Clear log error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def _register_socketio_events(self):
        """Register SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info(f"Client connected: {request.sid}")
            # Send initial status
            status = self.execution_manager.get_status()
            emit('status_update', status)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info(f"Client disconnected: {request.sid}")
        
        @self.socketio.on('request_status')
        def handle_status_request():
            status = self.execution_manager.get_status()
            emit('status_update', status)
    
    def _broadcast_status(self, status: Dict[str, Any]):
        """
        Broadcast status update to all connected clients
        
        Args:
            status: Status dictionary
        """
        try:
            # For threading mode, emit without broadcast parameter
            self.socketio.emit('status_update', status, namespace='/')
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False):
        """
        Run the web server
        
        Args:
            host: Host address
            port: Port number
            debug: Debug mode
        """
        logger.info(f"Starting web server on {host}:{port}")
        self.socketio.run(
            self.app, 
            host=host, 
            port=port, 
            debug=debug,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    
    def stop(self):
        """Stop the web server"""
        logger.info("Stopping web server")
        # SocketIO cleanup handled automatically


def create_web_server(execution_manager: ExecutionManager, config: Dict[str, Any], gpio_monitor=None) -> WebServer:
    """
    Factory function to create web server
    
    Args:
        execution_manager: Execution manager instance
        config: Web server configuration
        gpio_monitor: GPIO monitor instance (optional)
    
    Returns:
        WebServer instance
    """
    return WebServer(execution_manager, config, gpio_monitor)
