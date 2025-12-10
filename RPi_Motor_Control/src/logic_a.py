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
        self.tala_pulsado = False  # Toggle state for drill in manual mode (Arduino behavior)
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
        
        # Manual mode indicator (GPIO 2)
        self.manual_mode_pin = 2
        self.hw.set_mode_output(self.manual_mode_pin, initial_value=0)
    
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
            # Only log if not overridden by child class
            if self.__class__.__name__ == "LogicA":
                logger.info("Logic A started")
    
    def stop(self):
        """Stop logic execution"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            
            # Reset state flags (emergency stop cleanup)
            self.en_ejecucion = False
            self.en_espera = False
            self.modo_manual = False
            self.mode = OperationMode.IDLE
            
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
        # Validate mode number
        if mode_number < 1 or mode_number > 5:
            logger.error(f"❌ Invalid mode number: {mode_number}")
            logger.error("   Valid modes are 1-5")
            return False
        
        # Check if execution is running
        if self.en_ejecucion:
            logger.warning(f"❌ Cannot change mode while execution is running")
            logger.warning("   Press STOP button first")
            return False
        
        # Check if in manual mode
        if self.modo_manual:
            logger.warning(f"❌ Cannot select mode while in manual mode")
            logger.warning("   Press MANUAL button to exit manual mode first")
            return False
        
        # Select mode and load parameters
        logger.info("="*60)
        logger.info(f"MODE {mode_number} SELECTED")
        logger.info("="*60)
        
        self.selected_mode = mode_number
        self.en_espera = True
        self.mode = OperationMode.WAITING
        
        # Load mode parameters from config (Arduino structure: nivel1-5)
        mode_key = f"nivel{mode_number}"
        
        # Display parameters from different config sections
        pasos_nivel1 = self.config['pasos_primer_nivel'].get(mode_key, 'N/A')
        pasos_intermedio = self.config['pasos_acomodo_segundo_nivel'].get(mode_key, 'N/A')
        pasos_nivel2 = self.config['pasos_segundo_nivel'].get(mode_key, 'N/A')
        vueltas_nivel1 = self.config['vueltas_primer_nivel'].get(mode_key, 'N/A')
        velocidad_lineal = self.config['velocidades_lineal'].get(mode_key, 'N/A')
        velocidad_taladro = self.config['velocidades_taladro'].get(mode_key, 'N/A')
        
        logger.info(f"✓ Mode {mode_number} parameters loaded:")
        logger.info(f"  - Cycle 1 revolutions: {vueltas_nivel1}")
        logger.info(f"  - Cycle 1 steps: {pasos_nivel1}")
        logger.info(f"  - Intermediate steps: {pasos_intermedio}")
        logger.info(f"  - Cycle 2 steps: {pasos_nivel2}")
        logger.info(f"  - Linear speed: {velocidad_lineal} µs")
        logger.info(f"  - Drill speed: {velocidad_taladro} µs")
        
        logger.info("✓ Status: WAITING FOR START BUTTON")
        logger.info("  Press START button to begin automatic execution")
        logger.info("="*60)
        
        self.csv_logger.log_operation("A", "Auto", f"Mode{mode_number}Selected", "Ready")
        self._update_status()
        
        return True
    
    def toggle_manual_mode(self):
        """Toggle manual mode on/off (Arduino-like behavior)"""
        if self.modo_manual:
            # Currently in manual mode - EXIT manual mode
            logger.info("="*60)
            logger.info("MANUAL BUTTON PRESSED - Exiting Manual Mode")
            logger.info("="*60)
            
            self.modo_manual = False
            self.tala_pulsado = False  # Reset drill toggle state
            self.motor_linear.stop()
            self.motor_drill.stop()
            self.mode = OperationMode.IDLE
            
            # Set GPIO 2 LOW when exiting manual mode
            self.hw.write(self.manual_mode_pin, 0)
            
            logger.info("✓ Manual mode DISABLED")
            logger.info(f"✓ GPIO {self.manual_mode_pin} set LOW")
            logger.info("✓ Drill motor stopped")
            logger.info("✓ Returned to automatic mode")
            logger.info("="*60)
            
            self.csv_logger.log_operation("A", "Manual", "ModeDisabled", "Inactive")
            self._update_status()
            
        else:
            # Not in manual mode - ENTER manual mode (if allowed)
            if self.en_ejecucion or self.en_espera:
                logger.warning("❌ Cannot enter manual mode - system is busy")
                logger.warning("   System is either executing or waiting for start")
                logger.warning("   Press RESET first to stop current operation")
                return False
            
            logger.info("="*60)
            logger.info("MANUAL BUTTON PRESSED - Entering Manual Mode")
            logger.info("="*60)
            
            self.modo_manual = True
            self.tala_pulsado = False  # Initialize drill toggle state
            self.mode = OperationMode.MANUAL
            
            # Set GPIO 2 HIGH to indicate manual mode
            self.hw.write(self.manual_mode_pin, 1)
            
            logger.info("✓ Manual mode ENABLED")
            logger.info(f"✓ GPIO {self.manual_mode_pin} set HIGH")
            logger.info("✓ Joystick controls linear motor")
            logger.info("✓ Tala button toggles drill motor (press once = ON, press again = OFF)")
            logger.info("✓ Press MANUAL again to exit")
            logger.info("="*60)
            
            self.csv_logger.log_operation("A", "Manual", "ModeEnabled", "Active")
            self._update_status()
            
        return True
    
    def enable_manual_mode(self):
        """Enable manual mode (for backward compatibility)"""
        if not self.modo_manual:
            return self.toggle_manual_mode()
        return True
    
    def disable_manual_mode(self):
        """Disable manual mode (for backward compatibility)"""
        if self.modo_manual:
            return self.toggle_manual_mode()
        return True
    
    def _main_loop(self):
        """Main execution loop (runs in separate thread)"""
        logger.info("Logic A main loop started")
        
        # ===== IMMEDIATELY FIND HOME ON STARTUP (Arduino behavior) =====
        logger.info("=== Initial Homing Sequence ===")
        self.encontrar_home()
        
        if not self._running:
            logger.info("Logic stopped during initial homing")
            return
        
        logger.info("✓ Home position reached")
        logger.info("=== Ready - Waiting for mode selection and START button ===")
        
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
        """Handle manual joystick control (Arduino-like behavior)"""
        # ===== TALA BUTTON TOGGLE (Arduino behavior) =====
        if self.btn_tala.check_rising_edge():
            self.tala_pulsado = not self.tala_pulsado
            if self.tala_pulsado:
                logger.info("✓ TALA button pressed - Drill motor ON")
            else:
                logger.info("✓ TALA button pressed - Drill motor OFF")
                self.motor_drill.stop()
        
        # ===== DRILL MOTOR CONTROL (Arduino behavior) =====
        if self.tala_pulsado and self.modo_manual:
            # Spin drill motor continuously when toggled ON
            velocidad_broca = self.config['velocidades_taladro'].get('manual', 2200)
            self.motor_drill.step_pulse(True)
            time.sleep(velocidad_broca / 1_000_000)
            self.motor_drill.step_pulse(False)
            time.sleep(velocidad_broca / 1_000_000)
        
        # ===== JOYSTICK LINEAR MOTOR CONTROL (Arduino behavior) =====
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
                
                # Actually step the motor (Arduino behavior)
                self.motor_linear.step_pulse(True)
                time.sleep(speed / 1_000_000)
                self.motor_linear.step_pulse(False)
                time.sleep(speed / 1_000_000)
            else:
                # At home limit - bounce back
                if self.limit_home.is_triggered():
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
                
                # Actually step the motor (Arduino behavior)
                self.motor_linear.step_pulse(True)
                time.sleep(speed / 1_000_000)
                self.motor_linear.step_pulse(False)
                time.sleep(speed / 1_000_000)
            else:
                # At final limit - bounce back
                if self.limit_final.is_triggered():
                    self._handle_final_limit_rebote()
        else:
            # Center - stop linear motor
            self.motor_linear.stop()
    
    def _handle_waiting_mode(self):
        """Handle waiting for start button (Arduino loop behavior)"""
        # Continuously check for start button press
        if self.btn_start.check_rising_edge():
            logger.info("="*60)
            logger.info("START BUTTON PRESSED")
            logger.info(f"Selected Mode: {self.selected_mode}")
            logger.info("="*60)
            
            # Check safety switch before starting (Arduino behavior)
            if not self.switch_s.is_triggered():
                logger.warning("⚠️  SAFETY SWITCH IS UNSAFE - Cannot start execution")
                logger.warning("   Safety switch must be HIGH (safe) to begin")
                logger.warning("   Waiting for safety switch HIGH + Start button press again...")
                self.motor_stop_switch()  # Wait for safety + start
                # After safety pause resolved, check if we should still start
                if not self.en_espera:
                    logger.info("Mode changed during safety pause - aborting start")
                    return
                # Don't auto-start, wait for another START press
                logger.info("Safety restored - press START button again to begin")
                return
            
            # Safety is good, proceed with execution
            logger.info("✓ Safety switch is SAFE (HIGH)")
            logger.info("✓ Beginning automatic execution...")
            
            self.en_espera = False
            self.en_ejecucion = True
            self.mode = OperationMode.RUNNING
            self._update_status()
            
            logger.info("Step 1: Finding home position...")
            # Find home position first (before starting execution)
            self.encontrar_home()
            
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
        Find home position - Arduino-like behavior
        - Checks if already at home first
        - Moves continuously until home sensor is triggered
        - Checks safety before EACH movement step
        - Stops immediately if safety becomes unsafe
        - Resumes automatically when safety is restored (NO START button needed)
        - Does NOT require START button press during homing
        """
        logic_name = "Logic A" if self.__class__.__name__ == "LogicA" else "Logic B"
        logger.info(f"{logic_name}: Finding home position")
        self.position_description = "Finding Home"
        self._update_status()
        
        # Check if already at home
        if self.limit_home.is_triggered():
            logger.info("✓ Already at home position")
            return
        
        logger.info("Moving towards home...")
        
        velocidad = self.config['velocidades_lineal']['home']
        sentido = self.config['motor_parameters']['sentido_giro_lineal']
        
        # Set direction toward home
        self.motor_linear.set_direction(sentido)
        
        # Move until home limit is triggered (Arduino loop behavior)
        while not self.limit_home.is_triggered() and self._running:
            # ===== SAFETY CHECK BEFORE EACH STEP (like Arduino) =====
            if not self.switch_s.is_triggered():
                # Safety is UNSAFE - stop motors immediately
                self.motor_linear.stop()
                logger.warning("⚠️  SAFETY UNSAFE during homing - motors stopped")
                logger.info("   Waiting for safety to restore (NO START button needed)...")
                
                # Wait for safety to be restored (auto-resume, no START needed)
                while not self.switch_s.is_triggered() and self._running:
                    time.sleep(0.1)  # Check every 100ms
                
                # Safety restored - log and continue
                if self._running:
                    logger.info("✓ Safety restored - resuming homing movement")
                continue
            
            # Check for stop button
            if self.btn_stop.check_rising_edge():
                logger.info("Stop button pressed during homing")
                self.motor_detenido_por_boton_stop()
                return
            
            # ===== SAFETY OK - MOVE ONE STEP =====
            self.motor_linear.step_pulse(True)
            time.sleep(velocidad / 1_000_000)
            self.motor_linear.step_pulse(False)
            time.sleep(velocidad / 1_000_000)
        
        # ===== HOME FOUND OR STOPPED =====
        # Stop motors
        self.motor_linear.stop()
        
        if self.limit_home.is_triggered():
            logger.info("✓ Home position found successfully")
        else:
            logger.warning("⚠️  Homing interrupted (stop signal received)")
            return
        
        # Move pasos_despues_home steps away from home
        logger.info("Moving to post-home position")
        pasos = self.config['pasos_home']['pasos_despues_home']
        
        # Create callback to check safety and stop button during post-home movement
        def post_home_check():
            """Check for stop conditions during post-home movement"""
            if self.btn_stop.check_rising_edge():
                self.motor_detenido_por_boton_stop()
                return True
            if not self.switch_s.is_triggered():
                # Safety unsafe - stop and wait (auto-resume, no START needed)
                self.motor_linear.stop()
                logger.warning("⚠️  SAFETY UNSAFE during post-home - waiting...")
                while not self.switch_s.is_triggered() and self._running:
                    time.sleep(0.1)
                if self._running:
                    logger.info("✓ Safety restored - continuing post-home movement")
                return False  # Continue after safety is restored
            return False
        
        self.motor_linear.step_blocking(pasos, velocidad, direction=not sentido, check_callback=post_home_check)
        
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
        """Handle safety switch pause - wait for safety HIGH AND start button press"""
        logger.critical("\u26d4 SAFETY PAUSE - System stopped")
        logger.critical("   Safety switch triggered (LOW = unsafe)")
        logger.warning("⏸️  Step 1: Waiting for safety switch to be HIGH (safe)...")
        self.position_description = "EN PAUSA"
        
        # Mark as not running during pause
        was_running = self.en_ejecucion
        self.en_ejecucion = False
        self._update_status()
        
        # Step 1: Wait for safety switch to return to safe state
        while not self.switch_s.is_triggered() and self._running:
            time.sleep(0.05)
        
        logger.info("✓ Safety switch is now HIGH (safe)")
        logger.warning("⏸️  Step 2: Waiting for Start button press to resume...")
        
        # Step 2: Wait for start button press
        while self._running:
            if self.btn_start.check_rising_edge():
                logger.info("✓ Start button pressed - resuming operation")
                # Restore running state
                self.en_ejecucion = was_running
                time.sleep(self.config['tiempos']['tiempo_para_empezar_despues_stop_ms'] / 1000)
                self._update_status()
                return
            time.sleep(0.01)
    
    def funcion_en_ejecucion(self):
        """
        Main execution function for automatic cycles (Arduino funcionEnEjecucion)
        Implements the complete automatic execution sequence:
        1. Initial delay with drill spinning
        2. Cycle 1 - Back and forth movements with drill
        3. Intermediate positioning
        4. Cycle 2 - Back and forth movements with drill pulses
        5. Wait for RESET button
        """
        try:
            logger.info("="*60)
            logger.info("AUTOMATIC EXECUTION STARTED")
            logger.info(f"Mode: {self.selected_mode}")
            logger.info("="*60)
            
            self.reset_pressed = False
            self.cycle_count = 0
            
            # Get mode-specific parameters from config (Arduino structure)
            # Mode 1-5 corresponds to nivel1-5 in config
            mode_key = f"nivel{self.selected_mode}"
            
            logger.info(f"Loading parameters for Mode {self.selected_mode} ({mode_key})...")
            
            # Extract parameters from different config sections
            pasos_nivel1 = self.config['pasos_primer_nivel'].get(mode_key, 0)
            pasos_intermedio = self.config['pasos_acomodo_segundo_nivel'].get(mode_key, 0)
            pasos_nivel2 = self.config['pasos_segundo_nivel'].get(mode_key, 0)
            vueltas_nivel1 = self.config['vueltas_primer_nivel'].get(mode_key, 0)
            velocidad_lineal = self.config['velocidades_lineal'].get(mode_key, 3000)
            velocidad_taladro = self.config['velocidades_taladro'].get(mode_key, 2200)
            
            logger.info(f"✓ Mode parameters:")
            logger.info(f"  - Cycle 1 steps: {pasos_nivel1}")
            logger.info(f"  - Intermediate steps: {pasos_intermedio}")
            logger.info(f"  - Cycle 2 steps: {pasos_nivel2}")
            logger.info(f"  - Cycle 1 revolutions: {vueltas_nivel1}")
            logger.info(f"  - Linear speed: {velocidad_lineal}")
            logger.info(f"  - Drill speed: {velocidad_taladro}")
            
            # Phase 1: Initial delay with drill spinning
            logger.info("\\n" + "="*60)
            logger.info("PHASE 1: Initial Delay with Drill Spinning")
            logger.info("="*60)
            if not self._execute_initial_delay(velocidad_taladro):
                return
            
            # Phase 2: Cycle 1 execution
            logger.info("\\n" + "="*60)
            logger.info("PHASE 2: Cycle 1 - Back and Forth with Drill")
            logger.info("="*60)
            if not self._execute_cycle_1(pasos_nivel1, vueltas_nivel1, velocidad_lineal, velocidad_taladro):
                return
            
            time.sleep(1.0)
            
            # Phase 3: Intermediate movement
            logger.info("\\n" + "="*60)
            logger.info("PHASE 3: Intermediate Positioning")
            logger.info("="*60)
            if not self._execute_intermediate_movement(pasos_intermedio, velocidad_lineal):
                return
            
            time.sleep(1.0)
            
            # Phase 4: Cycle 2 execution
            logger.info("\\n" + "="*60)
            logger.info("PHASE 4: Cycle 2 - Back and Forth with Drill Pulses")
            logger.info("="*60)
            if not self._execute_cycle_2(pasos_nivel2, velocidad_lineal, velocidad_taladro):
                return
            
            # Phase 5: Wait for reset button
            logger.info("\\n" + "="*60)
            logger.info("EXECUTION COMPLETE - Waiting for RESET")
            logger.info("="*60)
            self._wait_for_reset()
            
        except Exception as e:
            logger.error(f"❌ Error in execution: {e}", exc_info=True)
            self.csv_logger.log_error("A", "Execution", str(e))
        finally:
            self.en_ejecucion = False
            self.mode = OperationMode.IDLE
            logger.info("✓ Automatic execution ended")
            self._update_status()
    
    def _execute_initial_delay(self, velocidad_taladro):
        """
        Execute initial delay with drill spinning (Arduino behavior)
        Drill spins for tiempo_antes_de_girar_ms before cycle starts
        """
        logger.info("⏱️  Starting initial delay with drill spinning...")
        self.cycle_phase = CyclePhase.INITIAL_DELAY
        self.position_description = "Initial Delay - Drill Spinning"
        self._update_status()
        
        delay_ms = self.config['tiempos']['tiempo_antes_de_girar_ms']
        logger.info(f"  Delay duration: {delay_ms}ms")
        
        start_time = time.time()
        elapsed = 0
        
        while self._running and elapsed < (delay_ms / 1000):
            # Check for stop/safety conditions
            if not self.switch_s.is_triggered():
                logger.warning("⚠️  Safety triggered during initial delay")
                self.motor_drill.stop()
                self.motor_stop_switch()
                if not self.en_ejecucion:
                    return False
                start_time = time.time()  # Reset timer after pause
                
            if self.btn_stop.check_rising_edge():
                logger.info("Stop button pressed during initial delay")
                self.motor_drill.stop()
                self.motor_detenido_por_boton_stop()
                if not self.en_ejecucion:
                    return False
                start_time = time.time()  # Reset timer after pause
            
            # Spin drill motor
            self.motor_drill.step_pulse(True)
            time.sleep(velocidad_taladro / 1_000_000)
            self.motor_drill.step_pulse(False)
            time.sleep(velocidad_taladro / 1_000_000)
            
            elapsed = time.time() - start_time
        
        # Check if we exited due to emergency stop
        if not self._running:
            logger.warning("⚠️  Initial delay interrupted by emergency stop")
            return False
        
        logger.info("✓ Initial delay complete")
        return True
    
    def _execute_cycle_1(self, pasos: int, vueltas: int, vel_lineal: int, vel_taladro: int):
        """
        Execute cycle 1 - Back and forth movements with drill rotation counting (Arduino behavior)
        - Linear motor moves back and forth for 'pasos' steps
        - Drill motor spins continuously
        - Counts drill revolutions (pasos_por_vuelta_taladro steps = 1 revolution)
        - Stops after 'vueltas' complete revolutions
        """
        logger.info(f"🔄 Starting Cycle 1:")
        logger.info(f"  - Steps per direction: {pasos}")
        logger.info(f"  - Target revolutions: {vueltas}")
        logger.info(f"  - Linear speed: {vel_lineal} µs")
        logger.info(f"  - Drill speed: {vel_taladro} µs")
        
        self.cycle_phase = CyclePhase.CYCLE_1
        self.position_description = "Cycle 1 - Back & Forth"
        self._update_status()
        self.csv_logger.log_operation("A", "Auto", "Cycle1", "Started")
        
        # Arduino variables
        hacia_final = True  # True = toward final, False = toward home
        conteo_pulsos_lineal = 0
        conteo_pulsos_taladro = 0
        conteo_vueltas = 0
        terminar_movimiento = False
        
        sentido_ciclos = self.config['motor_parameters'].get('sentido_ciclos', False)
        pasos_por_vuelta_taladro = self.config.get('pasos_por_vuelta_taladro', 400)
        
        last_linear_time = time.time()
        last_drill_time = time.time()
        estado_pulso_lineal = False
        estado_pulso_taladro = False
        
        while self._running:
            current_time = time.time()
            
            # Check safety and stop conditions
            if not self.switch_s.is_triggered():
                logger.warning("⚠️  Safety triggered during Cycle 1")
                self.motor_linear.stop()
                self.motor_drill.stop()
                self.motor_stop_switch()
                if not self.en_ejecucion:
                    return False
                last_linear_time = current_time
                last_drill_time = current_time
                continue
                
            if self.btn_stop.check_rising_edge():
                logger.info("Stop button pressed during Cycle 1")
                self.motor_linear.stop()
                self.motor_drill.stop()
                self.motor_detenido_por_boton_stop()
                if not self.en_ejecucion:
                    return False
                last_linear_time = current_time
                last_drill_time = current_time
                continue
            
            # Set linear motor direction
            if hacia_final:
                self.motor_linear.set_direction(not sentido_ciclos)
            else:
                self.motor_linear.set_direction(sentido_ciclos)
            
            # Step drill motor (continuous)
            if not terminar_movimiento and (current_time - last_drill_time) >= (vel_taladro / 1_000_000):
                last_drill_time = current_time
                estado_pulso_taladro = not estado_pulso_taladro
                self.motor_drill.step_pulse(estado_pulso_taladro)
                
                if estado_pulso_taladro:
                    conteo_pulsos_taladro += 1
                    
                    # Count complete revolutions
                    if conteo_pulsos_taladro >= pasos_por_vuelta_taladro:
                        conteo_pulsos_taladro = 0
                        conteo_vueltas += 1
                        logger.info(f"  Revolution {conteo_vueltas}/{vueltas} complete")
                        self._update_status()
                        
                        # Check if target revolutions reached
                        if conteo_vueltas >= vueltas:
                            conteo_vueltas = 0
                            terminar_movimiento = True
                            logger.info("  ✓ Target revolutions reached - finishing current pass")
            
            # Step linear motor
            if (current_time - last_linear_time) >= (vel_lineal / 1_000_000):
                last_linear_time = current_time
                estado_pulso_lineal = not estado_pulso_lineal
                self.motor_linear.step_pulse(estado_pulso_lineal)
                
                if estado_pulso_lineal:
                    conteo_pulsos_lineal += 1
            
            # Check if reached end of current pass
            if conteo_pulsos_lineal >= pasos:
                hacia_final = not hacia_final
                conteo_pulsos_lineal = 0
                direction_str = "toward final" if hacia_final else "toward home"
                logger.info(f"  Direction changed: {direction_str}")
                
                # Exit condition: finished movement and returning to start
                if terminar_movimiento and hacia_final:
                    break
        
        # Stop motors
        self.motor_linear.stop()
        self.motor_drill.stop()
        
        # Check if we exited due to emergency stop
        if not self._running:
            logger.warning("⚠️  Cycle 1 interrupted by emergency stop")
            return False
        
        logger.info("✓ Cycle 1 complete")
        self.csv_logger.log_operation("A", "Auto", "Cycle1", "Completed", cycle_count=vueltas)
        return True
    
    def _execute_intermediate_movement(self, pasos: int, velocidad: int):
        """
        Execute intermediate positioning movement (Arduino behavior)
        Moves linear motor forward to position for Cycle 2
        """
        logger.info(f"↗️  Starting intermediate positioning:")
        logger.info(f"  - Steps: {pasos}")
        logger.info(f"  - Speed: {velocidad} µs")
        
        self.cycle_phase = CyclePhase.INTERMEDIATE
        self.position_description = "Intermediate Positioning"
        self._update_status()
        
        sentido_ciclos = self.config['motor_parameters'].get('sentido_ciclos', False)
        self.motor_linear.set_direction(not sentido_ciclos)  # Toward final
        
        conteo_pulsos = 0
        last_time = time.time()
        estado_pulso = False
        
        while self._running and conteo_pulsos < (pasos * 2):  # *2 because we count rising and falling edges
            current_time = time.time()
            
            # Check safety and stop conditions
            if not self.switch_s.is_triggered():
                logger.warning("⚠️  Safety triggered during intermediate movement")
                self.motor_linear.stop()
                self.motor_stop_switch()
                if not self.en_ejecucion:
                    return False
                last_time = current_time
                continue
                
            if self.btn_stop.check_rising_edge():
                logger.info("Stop button pressed during intermediate movement")
                self.motor_linear.stop()
                self.motor_detenido_por_boton_stop()
                if not self.en_ejecucion:
                    return False
                last_time = current_time
                continue
            
            # Step motor
            if (current_time - last_time) >= (velocidad / 1_000_000):
                last_time = current_time
                estado_pulso = not estado_pulso
                self.motor_linear.step_pulse(estado_pulso)
                conteo_pulsos += 1
        
        self.motor_linear.stop()
        
        # Check if we exited due to emergency stop
        if not self._running:
            logger.warning("⚠️  Intermediate positioning interrupted by emergency stop")
            return False
        
        logger.info("✓ Intermediate positioning complete")
        return True
    
    def _execute_cycle_2(self, pasos: int, velocidad: int, vel_taladro: int):
        """
        Execute cycle 2 - Back and forth with drill pulses at each direction change (Arduino behavior)
        - Linear motor moves back and forth for 'pasos' steps
        - Drill motor pulses at each direction change (not continuous)
        - Counts cycles (cantidadGirosTaladroCiclo2 times)
        """
        logger.info(f"🔄 Starting Cycle 2:")
        logger.info(f"  - Steps per direction: {pasos}")
        logger.info(f"  - Speed: {velocidad} µs")
        
        self.cycle_phase = CyclePhase.CYCLE_2
        self.position_description = "Cycle 2 - Pulsed Drill"
        self._update_status()
        self.csv_logger.log_operation("A", "Auto", "Cycle2", "Started")
        
        # Arduino variables for Cycle 2
        hacia_final = True
        conteo_pulsos = 0
        conteo_vueltas = 0
        terminar_movimiento = False
        
        sentido_ciclos = self.config['motor_parameters'].get('sentido_ciclos', False)
        cantidad_giros_ciclo2 = self.config.get('cantidad_giros_taladro_ciclo_2', 3)
        pasos_taladro_ciclo2 = self.config.get('pasos_taladro_ciclo_2', 200)
        velocidad_pasos_taladro_ciclo2 = self.config.get('velocidad_pasos_taladro_ciclo_2', 2200)
        
        logger.info(f"  - Target cycles: {cantidad_giros_ciclo2}")
        logger.info(f"  - Drill pulses per cycle: {pasos_taladro_ciclo2}")
        
        last_time = time.time()
        estado_pulso = False
        
        while self._running:
            current_time = time.time()
            
            # Check safety and stop conditions
            if not self.switch_s.is_triggered():
                logger.warning("⚠️  Safety triggered during Cycle 2")
                self.motor_linear.stop()
                self.motor_stop_switch()
                if not self.en_ejecucion:
                    return False
                last_time = current_time
                continue
                
            if self.btn_stop.check_rising_edge():
                logger.info("Stop button pressed during Cycle 2")
                self.motor_linear.stop()
                self.motor_detenido_por_boton_stop()
                if not self.en_ejecucion:
                    return False
                last_time = current_time
                continue
            
            # Set linear motor direction
            if hacia_final:
                self.motor_linear.set_direction(not sentido_ciclos)
            else:
                self.motor_linear.set_direction(sentido_ciclos)
            
            # Step linear motor
            if (current_time - last_time) >= (velocidad / 1_000_000):
                last_time = current_time
                estado_pulso = not estado_pulso
                self.motor_linear.step_pulse(estado_pulso)
                
                if estado_pulso:
                    conteo_pulsos += 1
            
            # Check if reached end of current pass
            if conteo_pulsos >= pasos:
                hacia_final = not hacia_final
                conteo_pulsos = 0
                direction_str = "toward final" if hacia_final else "toward home"
                logger.info(f"  Direction changed: {direction_str}")
                
                # Pulse drill motor when returning to start (Arduino behavior)
                if not terminar_movimiento and hacia_final:
                    conteo_vueltas += 1
                    logger.info(f"  Cycle {conteo_vueltas}/{cantidad_giros_ciclo2} - Pulsing drill...")
                    
                    # Pulse drill for pasos_taladro_ciclo2 steps
                    for i in range(pasos_taladro_ciclo2):
                        self.motor_drill.step_pulse(True)
                        time.sleep(velocidad_pasos_taladro_ciclo2 / 1_000_000)
                        self.motor_drill.step_pulse(False)
                        time.sleep(velocidad_pasos_taladro_ciclo2 / 1_000_000)
                    
                    logger.info(f"  ✓ Cycle {conteo_vueltas} complete")
                
                # Exit condition: finished all cycles and returning to start
                if terminar_movimiento and hacia_final:
                    break
            
            # Check if target cycles reached
            if conteo_vueltas >= cantidad_giros_ciclo2:
                conteo_vueltas = 0
                terminar_movimiento = True
                logger.info("  ✓ Target cycles reached - finishing current pass")
        
        self.motor_linear.stop()
        
        # Check if we exited due to emergency stop
        if not self._running:
            logger.warning("⚠️  Cycle 2 interrupted by emergency stop")
            return False
        
        logger.info("✓ Cycle 2 complete")
        self.csv_logger.log_operation("A", "Auto", "Cycle2", "Completed")
        return True
    
    def _wait_for_reset(self):
        """
        Wait for reset button press after cycle completion (Arduino behavior)
        System waits at completion screen until RESET is pressed
        """
        logger.info("="*60)
        logger.info("🎉 EXECUTION COMPLETE")
        logger.info("   Waiting for RESET button press...")
        logger.info("="*60)
        
        self.cycle_phase = CyclePhase.COMPLETE
        self.position_description = "Complete - Press RESET"
        self._update_status()
        
        conteo_veces_reset = 0
        
        while conteo_veces_reset == 0 and self._running:
            # Only allow RESET when safety is HIGH (Arduino behavior)
            if self.switch_s.is_triggered():
                if self.btn_reset.check_rising_edge():
                    logger.info("✓ RESET button pressed - Finding home...")
                    conteo_veces_reset += 1
                    self._handle_reset()
                    return
            
            time.sleep(0.01)
    
    def _check_stop_conditions(self) -> bool:
        """Check for stop/safety conditions"""
        if self.btn_stop.check_rising_edge():
            self.motor_detenido_por_boton_stop()
            return True
        
        if not self.switch_s.is_triggered():
            # Safety switch triggered - pause and wait, then continue (don't exit)
            self.motor_stop_switch()
            return False  # Continue after safety pause is resolved
        
        return False
    
    def _update_status(self):
        """Update status and notify callback if set"""
        if self.status_callback:
            # Determine display mode
            if self.selected_mode > 0:
                display_mode = f"Mode {self.selected_mode}"
            else:
                display_mode = self.mode.value
            
            status = {
                'logic': 'A',
                'mode': display_mode,
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
        # Determine display mode: "Mode 1-5" or internal state
        if self.selected_mode > 0:
            display_mode = f"Mode {self.selected_mode}"
        else:
            display_mode = self.mode.value
        
        return {
            'logic': 'A',
            'mode': display_mode,
            'phase': self.cycle_phase.value if hasattr(self, 'cycle_phase') else 'idle',
            'position': self.position_description,
            'cycle_count': self.cycle_count,
            'selected_mode': self.selected_mode,
            'manual_mode': self.modo_manual,
            'tala_active': self.tala_pulsado,  # Drill toggle state in manual mode
            'running': self.en_ejecucion,  # This is the execution running status
            'waiting': self.en_espera,
            'active': self._running  # This is the main thread running status
        }
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop()
        logger.info("Logic A cleanup complete")
