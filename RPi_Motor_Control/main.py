"""
RPi Motor Control System - Main Entry Point
Initializes hardware, logics, and web server
"""

import sys
import signal
import logging
import argparse
import json
import os
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.hardware_interface import get_hardware_interface
from src.logger import init_csv_logger
from src.execution_manager import create_execution_manager
from src.web_server import create_web_server
from src.gpio_monitor import GPIOMonitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/system.log')
    ]
)

# Suppress Flask/Werkzeug HTTP request logs (only show warnings and errors)
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class MotorControlSystem:
    """Main system controller"""
    
    def __init__(self, simulate: bool = False, debug: bool = False):
        """
        Initialize motor control system
        
        Args:
            simulate: Run in simulation mode (no real hardware)
            debug: Enable debug logging
        """
        self.simulate = simulate
        self.debug = debug
        
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.debug("Debug mode enabled")
        
        # Load system configuration
        self.system_config = self._load_system_config()
        
        # Override simulation from config if specified
        if self.system_config.get('system', {}).get('simulation_mode', False):
            self.simulate = True
        
        logger.info(f"Starting Motor Control System (simulate={self.simulate})")
        
        # Initialize components
        self.hw_interface = None
        self.csv_logger = None
        self.gpio_monitor = None
        self.execution_manager = None
        self.web_server = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _load_system_config(self) -> dict:
        """Load system configuration"""
        config_path = Path(__file__).parent / 'config' / 'system_config.json'
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded system configuration from {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load system config: {e}")
            logger.warning("Using default configuration")
            return {
                'system': {'simulation_mode': False, 'debug_mode': False},
                'web_server': {'host': '0.0.0.0', 'port': 5000, 'engineer_password': '1234'},
                'logging': {'operations_log': 'logs/operations_{date}.csv'}
            }
    
    def _check_startup_safety(self):
        """Check safety switch at startup and wait for safe state + start button if unsafe"""
        # GPIO 6 is the safety switch - active HIGH = safe, LOW = unsafe
        SAFETY_SWITCH_PIN = 6
        
        safety_state = self.hw_interface.read(SAFETY_SWITCH_PIN)
        
        if not safety_state:  # LOW = unsafe
            logger.warning("\u26a0\ufe0f  SAFETY SWITCH UNSAFE at startup (GPIO 6 = LOW)")
            logger.warning("   System will wait for safety HIGH + Start button before continuing...")
            
            # Create temporary button to wait for start
            START_BUTTON_PIN = 23
            from src.motor_controller import Button
            btn_start = Button(self.hw_interface, START_BUTTON_PIN, "Start")
            
            # Step 1: Wait for safety switch to be HIGH
            logger.warning("⏸️  Step 1: Waiting for safety switch to be HIGH (safe)...")
            while not self.hw_interface.read(SAFETY_SWITCH_PIN):
                time.sleep(0.05)
            
            logger.info("✓ Safety switch is now HIGH (safe)")
            
            # Step 2: Wait for Start button
            logger.warning("⏸️  Step 2: Press Start button to continue startup...")
            while True:
                if btn_start.check_rising_edge():
                    logger.info("✓ Start button pressed - continuing startup")
                    break
                time.sleep(0.01)
        else:
            logger.info("✓ Safety switch is safe at startup (GPIO 6 = HIGH)")
    
    def initialize(self):
        """Initialize all system components"""
        try:
            logger.info("Initializing system components...")
            
            # 1. Initialize hardware interface
            logger.info("Initializing hardware interface...")
            self.hw_interface = get_hardware_interface(simulate=self.simulate)
            
            # 2. Initialize CSV logger
            logger.info("Initializing CSV logger...")
            log_dir = Path(self.system_config.get('logging', {}).get('operations_log', 'logs/operations.csv')).parent
            self.csv_logger = init_csv_logger(str(log_dir))
            
            # 3. Initialize GPIO monitor
            logger.info("Initializing GPIO monitor...")
            self.gpio_monitor = GPIOMonitor(self.hw_interface, self.system_config)
            
            # 4. Check safety switch at startup (matches Arduino setup())
            logger.info("Checking safety switch at startup...")
            self._check_startup_safety()
            
            # 5. Initialize execution manager
            logger.info("Initializing execution manager...")
            config_dir = Path(__file__).parent / 'config'
            config_a_path = config_dir / 'config_logic_a.json'
            config_b_path = config_dir / 'config_logic_b.json'
            
            self.execution_manager = create_execution_manager(
                self.hw_interface,
                str(config_a_path),
                str(config_b_path),
                self.csv_logger
            )
            
            # 6. Initialize web server
            logger.info("Initializing web server...")
            web_config = self.system_config.get('web_server', {})
            self.web_server = create_web_server(self.execution_manager, web_config, self.gpio_monitor)
            
            logger.info("System initialization complete")
            self.csv_logger.log_operation("System", "Startup", "Initialize", "Success")
            
        except Exception as e:
            logger.critical(f"System initialization failed: {e}", exc_info=True)
            if self.csv_logger:
                self.csv_logger.log_error("System", "Startup", str(e))
            raise
    
    def run(self):
        """Run the system"""
        try:
            logger.info("="*60)
            logger.info("RPi Motor Control System Starting")
            logger.info(f"Mode: {'SIMULATION' if self.simulate else 'PRODUCTION'}")
            logger.info("="*60)
            
            # Get web server config
            web_config = self.system_config.get('web_server', {})
            host = web_config.get('host', '0.0.0.0')
            port = web_config.get('port', 5000)
            
            logger.info(f"Web interface will be available at: http://{host}:{port}")
            if not self.simulate:
                logger.info("WiFi AP (if configured): http://192.168.4.1:5000")
            
            # Start web server (blocking)
            self.web_server.run(host=host, port=port, debug=self.debug)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.critical(f"System error: {e}", exc_info=True)
            if self.csv_logger:
                self.csv_logger.log_error("System", "Runtime", str(e))
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Gracefully shutdown the system"""
        logger.info("Shutting down system...")
        
        try:
            if self.execution_manager:
                logger.info("Stopping execution manager...")
                self.execution_manager.emergency_stop_all()
                self.execution_manager.cleanup()
            
            if self.web_server:
                logger.info("Stopping web server...")
                self.web_server.stop()
            
            if self.hw_interface:
                logger.info("Cleaning up hardware interface...")
                self.hw_interface.cleanup()
            
            if self.csv_logger:
                self.csv_logger.log_operation("System", "Shutdown", "Cleanup", "Success")
            
            logger.info("System shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}", exc_info=True)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        logger.info(f"Received signal {signum}")
        self.shutdown()
        sys.exit(0)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='RPi Motor Control System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in simulation mode (no hardware required)
  python main.py --simulate

  # Run in production mode with debug logging
  python main.py --debug

  # Run with custom port
  python main.py --port 8080

  # Run in simulation with debug
  python main.py --simulate --debug
        """
    )
    
    parser.add_argument(
        '--simulate',
        action='store_true',
        help='Run in simulation mode (no real hardware)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Web server port (default: 5000)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Web server host (default: 0.0.0.0)'
    )
    
    args = parser.parse_args()
    
    # Create and run system
    system = MotorControlSystem(simulate=args.simulate, debug=args.debug)
    
    try:
        system.initialize()
        
        # Override web server config from CLI args
        if args.port != 5000 or args.host != '0.0.0.0':
            system.system_config['web_server']['port'] = args.port
            system.system_config['web_server']['host'] = args.host
        
        system.run()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
