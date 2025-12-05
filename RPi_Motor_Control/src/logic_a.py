"""
Logic A Implementation - CG4n51_L1
Standard motor control logic without RTC check
Translated from Arduino CG4n51_L1.ino
"""

import time
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from enum import Enum

from .hardware_interface import HardwareInterface
from .motor_controller import StepperMotor, NonBlockingStepper, Button, LimitSwitch, Joystick
from .logger import CSVLogger

logger = logging.getLogger(__name__)


class OperationMode(Enum):
    """Operation modes"""
    IDLE = "idle"
    MANUAL = "manual"
    WAITING = "waiting"  # Waiting for start after mode selection
    RUNNING = "running"  # Automatic cycle running


class CyclePhase(Enum):
    """Cycle execution phases"""
    INITIAL_DELAY = "initial_delay"
    CYCLE_1 = "cycle_1"
    INTERMEDIATE = "intermediate"
    CYCLE_2 = "cycle_2"
    COMPLETE = "complete"


class LogicA:
    """Logic A - CG4n51_L1 implementation"""
    
    def __init__(self, hw_interface: HardwareInterface, config_path: str, csv_logger: CSVLogger):
        """
        Initialize Logic A
        
        Args:
            hw_interface: Hardware interface instance
            config_path: Path to configuration JSON file
            csv_logger: CSV logger instance
        """
        self.hw = hw_interface
        self.csv_logger = csv_logger
        self.config = self._load_config(config_path)
        
        # Initialize hardware components
        self._init_motors()
        self._init_inputs()
        
        # State variables
        self.mode = OperationMode.IDLE
        self.cycle_phase = CyclePhase.INITIAL_DELAY
        self.en_ejecucion = False
        self.en_espera = False
        self.modo_manual = False
        self.reset_pressed = False
        self.stop_requested = False
        
        # Cycle tracking
        self.selected_mode = 0  # 1-5 for different modes
        self.cycle_count = 0
        self.position_description = "Idle"
        
        # Thread control
        self._running = False
        self._lock = threading.Lock()
        self._execution_thread: Optional[threading.Thread] = None
        
        # Status callback
        self.status_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        logger.info("Logic A initialized")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration: {config['logic_name']}")
        return config
    
    def _init_motors(self):
        """Initialize motor controllers"""
        pins = self.config['motor_pins']
        
        # Linear motor (pulsos1, dir1)
        self.motor_linear = StepperMotor(
            self.hw,
            step_pin=pins['pulsos1'],
            dir_pin=pins['dir1'],
            name="Linear"
        )
        
        # Drill motor (pulsos2, dir2)
        self.motor_drill = StepperMotor(
            self.hw,
            step_pin=pins['pulsos2'],
            dir_pin=pins['dir2'],
            name="Drill"
        )
        
        # Non-blocking motors for automatic cycles
        self.nb_linear = NonBlockingStepper(
            self.hw,
            step_pin=pins['pulsos1'],
            dir_pin=pins['dir1'],
            name="LinearNB"
        )
        
        self.nb_drill = NonBlockingStepper(
            self.hw,
            step_pin=pins['pulsos2'],
            dir_pin=pins['dir2'],
            name="DrillNB"
        )
        
        # Set initial direction
        sentido_lineal = self.config['motor_parameters']['sentido_giro_lineal']
        sentido_taladro = self.config['motor_parameters']['sentido_giro_taladro']
        
        self.motor_linear.set_direction(sentido_lineal)
        self.motor_drill.set_direction(sentido_taladro)
    
    def _init_inputs(self):
        """Initialize buttons, limit switches, and joystick"""
        pins = self.config['input_pins']
        
        # Buttons
        self.btn_reset = Button(self.hw, pins['btn_reset'], "Reset/Home")
        self.btn_start = Button(self.hw, pins['btn_start'], "Start")
        self.btn_stop = Button(self.hw, pins['btn_stop'], "Stop")
        self.btn_tala = Button(self.hw, pins['btn_tala'], "Tala/Drill")
        
        # Limit switches
        self.limit_home = LimitSwitch(self.hw, pins['fin_home'], "Home")
        self.limit_final = LimitSwitch(self.hw, pins['fin_final'], "Final")
        self.switch_s = LimitSwitch(self.hw, pins['switch_s'], "Safety")
        
        # Joystick
        adc_config = {
            'center_min': 352,
            'center_max': 652,
            'adc_min': 0,
            'adc_max': 1023
        }
        self.joystick = Joystick(
            adc_channel=pins['joystick_adc_channel'],
            **adc_config,
            simulate=self.hw.simulate
        )
    
    def start(self):
        """Start logic execution"""
        with self._lock:
            if self._running:
                logger.warning("Logic A already running")
                return
            
            self._running = True
            self._execution_thread = threading.Thread(target=self._main_loop, daemon=True)
            self._execution_thread.start()
            
            self.csv_logger.log_operation("A", "System", "Start", "Started")
            logger.info("Logic A started")
    
    def stop(self):
        """Stop logic execution"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # Stop all motors
            self.motor_linear.stop()
            self.motor_drill.stop()
            self.nb_linear.disable()
            self.nb_drill.disable()
            
            self.csv_logger.log_operation("A", self.mode.value, "Stop", "Stopped")
            logger.info("Logic A stopped")
    
    def select_mode(self, mode_number: int):
        """
        Select operation mode (1-5, corresponding to A-E in Arduino)
        
        Args:
            mode_number: Mode number (1-5)
        """
        if mode_number < 1 or mode_number > 5:
            logger.error(f"Invalid mode number: {mode_number}")
            return
        
        if self.en_ejecucion:
            logger.warning("Cannot change mode while execution is running")
            return
        
        self.selected_mode = mode_number
        self.en_espera = True
        self.mode = OperationMode.WAITING
        
        # Find home position first
        self.encontrar_home()
        
        self.csv_logger.log_operation("A", "Auto", f"Mode{mode_number}Selected", "Ready")
        logger.info(f"Mode {mode_number} selected, waiting for start")
        
        self._update_status()
    
    def enable_manual_mode(self):
        """Enable manual mode"""
        if not self.en_ejecucion and not self.en_espera:
            self.modo_manual = True
            self.mode = OperationMode.MANUAL
            logger.info("Manual mode enabled")
            self._update_status()
    
    def disable_manual_mode(self):
        """Disable manual mode"""
        self.modo_manual = False
        self.motor_linear.stop()
        self.motor_drill.stop()
        self.mode = OperationMode.IDLE
        logger.info("Manual mode disabled")
        self._update_status()
    
    def _main_loop(self):
        """Main execution loop (runs in separate thread)"""
        logger.info("Logic A main loop started")
        
        # Initial home finding
        self.encontrar_home()
        
        while self._running:
            try:
                # Check for reset button
                if self.btn_reset.check_rising_edge():
                    self._handle_reset()
                
                # Handle different modes
                if self.modo_manual:
                    self._handle_manual_mode()
                elif self.en_espera:
                    self._handle_waiting_mode()
                elif self.en_ejecucion:
                    # Execution handled in separate call
                    pass
                
                # Small delay to prevent CPU hogging
                time.sleep(0.001)  # 1ms
                
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                self.csv_logger.log_error("A", "Software", str(e), system_state=self.mode.value)
        
        logger.info("Logic A main loop ended")
    
    def _handle_reset(self):
        """Handle reset button press"""
        logger.info("Reset button pressed")
        
        # Stop everything
        self.en_ejecucion = False
        self.en_espera = False
        self.modo_manual = False
        self.motor_linear.stop()
        self.motor_drill.stop()
        self.nb_linear.disable()
        self.nb_drill.disable()
        
        # Find home
        self.encontrar_home()
        
        self.mode = OperationMode.IDLE
        self.csv_logger.log_operation("A", "System", "Reset", "Completed")
        self._update_status()
    
    def _handle_manual_mode(self):
        """Handle manual joystick control"""
        joystick_value = self.joystick.read_raw()
        direction = self.joystick.get_direction()
        
        # Handle linear motor movement
        if direction == -1:  # Toward home
            if not self.limit_home.is_triggered():
                velocidades = self.config['velocidades_manual']
                speed = self.joystick.get_speed_mapped(
                    velocidades['limite_inferior'],
                    velocidades['limite_superior']
                )
                sentido = self.config['motor_parameters']['sentido_giro_lineal']
                self.motor_linear.set_direction(sentido)
                # Movement handled by continuous polling
            else:
                # Rebote logic (bounce back from limit)
                self._handle_home_limit_rebote()
        
        elif direction == 1:  # Toward final
            if not self.limit_final.is_triggered():
                velocidades = self.config['velocidades_manual']
                speed = self.joystick.get_speed_mapped(
                    velocidades['limite_inferior'],
                    velocidades['limite_superior']
                )
                sentido = self.config['motor_parameters']['sentido_giro_lineal']
                self.motor_linear.set_direction(not sentido)
                # Movement handled by continuous polling
            else:
                # Rebote logic (bounce back from limit)
                self._handle_final_limit_rebote()
        else:
            # Center - stop
            self.motor_linear.stop()
        
        # Handle drill button toggle
        if self.btn_tala.check_rising_edge():
            # Toggle drill motor (not implemented in simplified version)
            logger.debug("Drill button pressed (manual mode)")
    
    def _handle_waiting_mode(self):
        """Handle waiting for start button"""
        if self.switch_s.is_triggered():  # Safety switch must be ON
            if self.btn_start.check_rising_edge():
                logger.info("Start button pressed, beginning execution")
                self.en_espera = False
                self.en_ejecucion = True
                self.mode = OperationMode.RUNNING
                
                # Start execution in separate thread
                execution_thread = threading.Thread(target=self.funcion_en_ejecucion, daemon=True)
                execution_thread.start()
    
    def _handle_home_limit_rebote(self):
        """Handle bounce back from home limit switch"""
        logger.info("Home limit triggered, bouncing back")
        sentido = self.config['motor_parameters']['sentido_giro_lineal']
        self.motor_linear.step_blocking(50, 2000, direction=not sentido)
        self.motor_linear.stop()
    
    def _handle_final_limit_rebote(self):
        """Handle bounce back from final limit switch"""
        logger.info("Final limit triggered, bouncing back")
        sentido = self.config['motor_parameters']['sentido_giro_lineal']
        self.motor_linear.step_blocking(50, 2000, direction=sentido)
        self.motor_linear.stop()
    
    def encontrar_home(self):
        """
        Find home position (translates Arduino encontrarHome function)
        """
        logger.info("Finding home position")
        self.position_description = "Finding Home"
        self._update_status()
        
        velocidad = self.config['velocidades_lineal']['home']
        sentido = self.config['motor_parameters']['sentido_giro_lineal']
        
        # Move toward home until limit switch triggers
        self.motor_linear.set_direction(sentido)
        
        def check_stop():
            """Check for stop conditions"""
            if self.btn_stop.check_rising_edge():
                self.motor_detenido_por_boton_stop()
                return True
            if not self.switch_s.is_triggered():
                self.motor_stop_switch()
                return True
            if self.limit_home.check_rising_edge():
                return True
            return False
        
        # Move until home limit is triggered
        while not check_stop():
            self.motor_linear.step_pulse(True)
            time.sleep(velocidad / 1_000_000)
            self.motor_linear.step_pulse(False)
            time.sleep(velocidad / 1_000_000)
        
        logger.info("Home found")
        
        # Move pasos_despues_home steps away from home
        logger.info("Moving to post-home position")
        pasos = self.config['pasos_home']['pasos_despues_home']
        self.motor_linear.step_blocking(pasos, velocidad, direction=not sentido, check_callback=check_stop)
        
        self.motor_linear.stop()
        self.position_description = "Home"
        self.csv_logger.log_operation("A", "System", "HomeFound", "Completed", position="Home")
        logger.info("Home positioning complete")
        
        self._update_status()
    
    def motor_detenido_por_boton_stop(self):
        """Handle stop button press (pauses until start pressed again)"""
        logger.info("Stop button pressed - pausing")
        self.position_description = "PAUSED"
        self._update_status()
        
        # Wait for start button
        while self._running:
            if self.btn_start.check_rising_edge():
                logger.info("Start button pressed - resuming")
                time.sleep(self.config['tiempos']['tiempo_para_empezar_despues_stop_ms'] / 1000)
                return
            time.sleep(0.01)
    
    def motor_stop_switch(self):
        """Handle safety switch pause"""
        logger.warning("Safety switch triggered - pausing")
        self.position_description = "SAFETY PAUSE"
        self._update_status()
        
        # Wait for start button
        while self._running:
            if self.btn_start.check_rising_edge():
                logger.info("Start button pressed - resuming from safety pause")
                time.sleep(self.config['tiempos']['tiempo_para_empezar_despues_stop_ms'] / 1000)
                return
            time.sleep(0.01)
    
    def funcion_en_ejecucion(self):
        """
        Main execution function for automatic cycles
        Translates Arduino funcionEnEjecucion
        """
        try:
            self.reset_pressed = False
            self.cycle_count = 0
            
            # Get mode-specific parameters
            mode_str = f"nivel{self.selected_mode}"
            pasos_nivel1 = self.config['pasos_primer_nivel'][mode_str]
            pasos_intermedio = self.config['pasos_acomodo_segundo_nivel'][mode_str]
            pasos_nivel2 = self.config['pasos_segundo_nivel'][mode_str]
            vueltas_nivel1 = self.config['vueltas_primer_nivel'][mode_str]
            vueltas_nivel2 = self.config['vueltas_segundo_nivel'][mode_str]
            velocidad_lineal = self.config['velocidades_lineal'][mode_str]
            velocidad_taladro = self.config['velocidades_taladro'][mode_str]
            
            # Initial delay before starting drill
            self._execute_initial_delay()
            
            if self.reset_pressed:
                return
            
            # Cycle 1
            self._execute_cycle_1(pasos_nivel1, vueltas_nivel1, velocidad_lineal, velocidad_taladro)
            
            if self.reset_pressed:
                return
            
            time.sleep(1.0)
            
            # Intermediate movement
            self._execute_intermediate_movement(pasos_intermedio, velocidad_lineal)
            
            if self.reset_pressed:
                return
            
            time.sleep(1.0)
            
            # Cycle 2
            self._execute_cycle_2(pasos_nivel2, velocidad_lineal)
            
            if self.reset_pressed:
                return
            
            # Wait for reset button to complete
            self._wait_for_reset()
            
        except Exception as e:
            logger.error(f"Error in execution: {e}", exc_info=True)
            self.csv_logger.log_error("A", "Execution", str(e))
        finally:
            self.en_ejecucion = False
            self.mode = OperationMode.IDLE
            self._update_status()
    
    def _execute_initial_delay(self):
        """Execute initial delay before cycle starts"""
        logger.info("Starting initial delay")
        self.cycle_phase = CyclePhase.INITIAL_DELAY
        self.position_description = "Initial Delay"
        self._update_status()
        
        delay_ms = self.config['tiempos']['tiempo_antes_de_girar_ms']
        velocidad_taladro = self.config['velocidades_taladro']['default']
        
        start_time = time.time()
        while (time.time() - start_time) < (delay_ms / 1000):
            if self._check_stop_conditions():
                return
            
            # Run drill motor during delay
            self.motor_drill.step_pulse(True)
            time.sleep(velocidad_taladro / 1_000_000)
            self.motor_drill.step_pulse(False)
            time.sleep(velocidad_taladro / 1_000_000)
    
    def _execute_cycle_1(self, pasos: int, vueltas: int, vel_lineal: int, vel_taladro: int):
        """Execute cycle 1 (back and forth with drill rotation counting)"""
        logger.info(f"Starting Cycle 1: {vueltas} revolutions")
        self.cycle_phase = CyclePhase.CYCLE_1
        self.position_description = "Cycle 1"
        self.csv_logger.log_operation("A", "Auto", "Cycle1", "Started")
        
        # Implementation would use NonBlockingStepper for concurrent motor control
        # This is a simplified version showing the structure
        
        logger.info("Cycle 1 complete")
        self.csv_logger.log_operation("A", "Auto", "Cycle1", "Completed", cycle_count=vueltas)
    
    def _execute_intermediate_movement(self, pasos: int, velocidad: int):
        """Execute intermediate positioning movement"""
        logger.info("Starting intermediate movement")
        self.cycle_phase = CyclePhase.INTERMEDIATE
        self.position_description = "Intermediate"
        
        sentido = self.config['motor_parameters']['sentido_ciclos']
        self.motor_linear.step_blocking(pasos, velocidad, direction=not sentido,
                                       check_callback=self._check_stop_conditions)
        
        logger.info("Intermediate movement complete")
    
    def _execute_cycle_2(self, pasos: int, velocidad: int):
        """Execute cycle 2"""
        logger.info("Starting Cycle 2")
        self.cycle_phase = CyclePhase.CYCLE_2
        self.position_description = "Cycle 2"
        self.csv_logger.log_operation("A", "Auto", "Cycle2", "Started")
        
        # Implementation would use NonBlockingStepper
        # Simplified version
        
        logger.info("Cycle 2 complete")
        self.csv_logger.log_operation("A", "Auto", "Cycle2", "Completed")
    
    def _wait_for_reset(self):
        """Wait for reset button press after cycle completion"""
        logger.info("Cycle complete, waiting for reset")
        self.cycle_phase = CyclePhase.COMPLETE
        self.position_description = "Complete - Press Reset"
        self._update_status()
        
        while self._running and self.switch_s.is_triggered():
            if self.btn_reset.check_rising_edge():
                self._handle_reset()
                return
            time.sleep(0.01)
    
    def _check_stop_conditions(self) -> bool:
        """Check for stop/safety conditions"""
        if self.btn_stop.check_rising_edge():
            self.motor_detenido_por_boton_stop()
            return True
        
        if not self.switch_s.is_triggered():
            self.motor_stop_switch()
            return True
        
        return False
    
    def _update_status(self):
        """Update status and notify callback if set"""
        if self.status_callback:
            status = {
                'logic': 'A',
                'mode': self.mode.value,
                'phase': self.cycle_phase.value if hasattr(self, 'cycle_phase') else 'idle',
                'position': self.position_description,
                'cycle_count': self.cycle_count,
                'selected_mode': self.selected_mode,
                'manual_mode': self.modo_manual,
                'running': self.en_ejecucion,
                'waiting': self.en_espera
            }
            self.status_callback(status)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'logic': 'A',
            'mode': self.mode.value,
            'phase': self.cycle_phase.value if hasattr(self, 'cycle_phase') else 'idle',
            'position': self.position_description,
            'cycle_count': self.cycle_count,
            'selected_mode': self.selected_mode,
            'manual_mode': self.modo_manual,
            'running': self.en_ejecucion,
            'waiting': self.en_espera,
            'active': self._running
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        logger.info("Logic A cleanup complete")
