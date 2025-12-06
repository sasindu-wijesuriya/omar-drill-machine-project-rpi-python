"""
Raspberry Pi GPIO Simulator
Web-based GPIO simulator for testing RPi applications locally
Runs on port 8100
"""

import json
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from threading import Lock
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'gpio-simulator-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# GPIO State Management
class GPIOSimulator:
    def __init__(self):
        self.lock = Lock()
        
        # Pin states: {pin_number: {'mode': 'INPUT'|'OUTPUT', 'value': 0|1, 'pull': 'OFF'|'UP'|'DOWN'}}
        self.pins = {}
        
        # Pin configurations from the RPi_Motor_Control project
        self.pin_configs = {
            # Motor pins (OUTPUT)
            18: {'name': 'pulsos1', 'type': 'MOTOR_PWM', 'default_mode': 'OUTPUT'},
            23: {'name': 'dir1', 'type': 'MOTOR_DIR', 'default_mode': 'OUTPUT'},
            24: {'name': 'pulsos2', 'type': 'MOTOR_PWM', 'default_mode': 'OUTPUT'},
            25: {'name': 'dir2', 'type': 'MOTOR_DIR', 'default_mode': 'OUTPUT'},
            
            # Input buttons (INPUT with PULL_UP)
            17: {'name': 'btnReset', 'type': 'BUTTON', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            27: {'name': 'btnStart', 'type': 'BUTTON', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            22: {'name': 'btnStop', 'type': 'BUTTON', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            5: {'name': 'btnTala', 'type': 'BUTTON', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            
            # Limit switches (INPUT with PULL_UP)
            13: {'name': 'finHome', 'type': 'LIMIT_SWITCH', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            19: {'name': 'finFinal', 'type': 'LIMIT_SWITCH', 'default_mode': 'INPUT', 'default_pull': 'UP'},
            6: {'name': 'switchS', 'type': 'SAFETY_SWITCH', 'default_mode': 'INPUT', 'default_pull': 'UP'},
        }
        
        # Initialize all configured pins
        for pin, config in self.pin_configs.items():
            self.pins[pin] = {
                'mode': config.get('default_mode', 'INPUT'),
                'value': 1 if config.get('default_pull') == 'UP' else 0,  # Pull-up default high
                'pull': config.get('default_pull', 'OFF'),
                'name': config['name'],
                'type': config['type']
            }
        
        logger.info(f"GPIO Simulator initialized with {len(self.pins)} pins")
    
    def set_mode(self, pin: int, mode: str):
        """Set pin mode (INPUT/OUTPUT)"""
        with self.lock:
            if pin not in self.pins:
                self.pins[pin] = {'mode': mode, 'value': 0, 'pull': 'OFF', 'name': f'GPIO{pin}', 'type': 'GENERIC'}
            else:
                self.pins[pin]['mode'] = mode
            logger.info(f"Pin {pin} mode set to {mode}")
            return True
    
    def set_pull(self, pin: int, pull: str):
        """Set pull-up/pull-down resistor"""
        with self.lock:
            if pin in self.pins:
                self.pins[pin]['pull'] = pull
                # Update value based on pull resistor
                if pull == 'UP':
                    self.pins[pin]['value'] = 1
                elif pull == 'DOWN':
                    self.pins[pin]['value'] = 0
                logger.info(f"Pin {pin} pull set to {pull}")
            return True
    
    def read(self, pin: int) -> int:
        """Read pin value"""
        with self.lock:
            if pin in self.pins:
                return self.pins[pin]['value']
            return 0
    
    def write(self, pin: int, value: int):
        """Write pin value"""
        with self.lock:
            if pin in self.pins:
                self.pins[pin]['value'] = value
                # Emit change via websocket
                socketio.emit('pin_changed', {
                    'pin': pin,
                    'value': value,
                    'timestamp': time.time()
                })
                return True
            return False
    
    def toggle_input(self, pin: int) -> int:
        """Toggle an input pin (for manual simulation)"""
        with self.lock:
            if pin in self.pins and self.pins[pin]['mode'] == 'INPUT':
                self.pins[pin]['value'] = 1 - self.pins[pin]['value']
                new_value = self.pins[pin]['value']
                logger.info(f"Pin {pin} ({self.pins[pin]['name']}) toggled to {new_value}")
                
                # Emit change via websocket
                socketio.emit('pin_changed', {
                    'pin': pin,
                    'value': new_value,
                    'timestamp': time.time()
                })
                return new_value
            return -1
    
    def set_input_value(self, pin: int, value: int) -> bool:
        """Set an input pin value (for manual simulation)"""
        with self.lock:
            if pin in self.pins and self.pins[pin]['mode'] == 'INPUT':
                self.pins[pin]['value'] = value
                logger.info(f"Pin {pin} ({self.pins[pin]['name']}) set to {value}")
                
                # Emit change via websocket
                socketio.emit('pin_changed', {
                    'pin': pin,
                    'value': value,
                    'timestamp': time.time()
                })
                return True
            return False
    
    def get_all_pins(self) -> dict:
        """Get all pin states"""
        with self.lock:
            return dict(self.pins)
    
    def get_pin_config(self, pin: int) -> dict:
        """Get pin configuration"""
        return self.pin_configs.get(pin, {})
    
    def reset(self):
        """Reset all pins to default state"""
        with self.lock:
            for pin, config in self.pin_configs.items():
                self.pins[pin] = {
                    'mode': config.get('default_mode', 'INPUT'),
                    'value': 1 if config.get('default_pull') == 'UP' else 0,
                    'pull': config.get('default_pull', 'OFF'),
                    'name': config['name'],
                    'type': config['type']
                }
            logger.info("GPIO Simulator reset to default state")
            socketio.emit('simulator_reset', {'timestamp': time.time()})


# Global simulator instance
gpio_sim = GPIOSimulator()


# Web Routes
@app.route('/')
def index():
    """Main simulator page"""
    return render_template('index.html')


@app.route('/api/pins', methods=['GET'])
def get_pins():
    """Get all pin states"""
    return jsonify({
        'pins': gpio_sim.get_all_pins(),
        'timestamp': time.time()
    })


@app.route('/api/pin/<int:pin>', methods=['GET'])
def get_pin(pin):
    """Get specific pin state"""
    pins = gpio_sim.get_all_pins()
    if pin in pins:
        return jsonify({
            'pin': pin,
            'state': pins[pin],
            'timestamp': time.time()
        })
    return jsonify({'error': 'Pin not found'}), 404


@app.route('/api/pin/<int:pin>/mode', methods=['POST'])
def set_pin_mode(pin):
    """Set pin mode"""
    data = request.get_json()
    mode = data.get('mode', 'INPUT').upper()
    
    if mode not in ['INPUT', 'OUTPUT']:
        return jsonify({'error': 'Invalid mode'}), 400
    
    gpio_sim.set_mode(pin, mode)
    return jsonify({
        'success': True,
        'pin': pin,
        'mode': mode
    })


@app.route('/api/pin/<int:pin>/pull', methods=['POST'])
def set_pin_pull(pin):
    """Set pin pull resistor"""
    data = request.get_json()
    pull = data.get('pull', 'OFF').upper()
    
    if pull not in ['OFF', 'UP', 'DOWN']:
        return jsonify({'error': 'Invalid pull value'}), 400
    
    gpio_sim.set_pull(pin, pull)
    return jsonify({
        'success': True,
        'pin': pin,
        'pull': pull
    })


@app.route('/api/pin/<int:pin>/value', methods=['GET', 'POST'])
def pin_value(pin):
    """Get or set pin value"""
    if request.method == 'GET':
        value = gpio_sim.read(pin)
        return jsonify({
            'pin': pin,
            'value': value,
            'timestamp': time.time()
        })
    else:
        data = request.get_json()
        value = data.get('value', 0)
        
        pins = gpio_sim.get_all_pins()
        if pin not in pins:
            return jsonify({'error': 'Pin not found'}), 404
        
        # Only allow setting input pins manually
        if pins[pin]['mode'] == 'INPUT':
            gpio_sim.set_input_value(pin, value)
            return jsonify({
                'success': True,
                'pin': pin,
                'value': value
            })
        else:
            return jsonify({'error': 'Can only manually set INPUT pins'}), 400


@app.route('/api/pin/<int:pin>/toggle', methods=['POST'])
def toggle_pin(pin):
    """Toggle input pin"""
    pins = gpio_sim.get_all_pins()
    if pin not in pins:
        return jsonify({'error': 'Pin not found'}), 404
    
    if pins[pin]['mode'] != 'INPUT':
        return jsonify({'error': 'Can only toggle INPUT pins'}), 400
    
    new_value = gpio_sim.toggle_input(pin)
    return jsonify({
        'success': True,
        'pin': pin,
        'value': new_value
    })


@app.route('/api/reset', methods=['POST'])
def reset_simulator():
    """Reset simulator to default state"""
    gpio_sim.reset()
    return jsonify({
        'success': True,
        'message': 'Simulator reset to default state'
    })


# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connected', {
        'message': 'Connected to GPIO Simulator',
        'pins': gpio_sim.get_all_pins()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')


@socketio.on('request_pins')
def handle_request_pins():
    """Send all pin states to client"""
    emit('pins_update', {
        'pins': gpio_sim.get_all_pins(),
        'timestamp': time.time()
    })


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Raspberry Pi GPIO Simulator")
    logger.info("Starting on http://localhost:8100")
    logger.info("=" * 60)
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
