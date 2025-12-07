"""
Execution Manager
Manages Logic A and Logic B execution with mutex locks
Ensures only one logic runs at a time with thread safety
"""

import threading
import logging
from typing import Optional, Dict, Any, Callable
from enum import Enum

from .hardware_interface import HardwareInterface
from .logic_a import LogicA
from .logic_b import LogicB
from .logger import CSVLogger

logger = logging.getLogger(__name__)


class ActiveLogic(Enum):
    """Currently active logic"""
    NONE = "none"
    LOGIC_A = "logic_a"
    LOGIC_B = "logic_b"


class ExecutionManager:
    """
    Manages execution of Logic A and Logic B
    Ensures mutual exclusion and thread safety
    """
    
    def __init__(self, hw_interface: HardwareInterface, 
                 config_a_path: str, config_b_path: str,
                 csv_logger: CSVLogger):
        """
        Initialize Execution Manager
        
        Args:
            hw_interface: Hardware interface instance (shared by both logics)
            config_a_path: Path to Logic A configuration
            config_b_path: Path to Logic B configuration
            csv_logger: CSV logger instance
        """
        self.hw = hw_interface
        self.csv_logger = csv_logger
        
        # Create logic instances
        self.logic_a = LogicA(hw_interface, config_a_path, csv_logger)
        self.logic_b = LogicB(hw_interface, config_b_path, csv_logger)
        
        # Execution state
        self._lock = threading.Lock()
        self._active_logic = ActiveLogic.NONE
        self._selected_logic = ActiveLogic.NONE
        
        # Status callback for web interface
        self.status_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        
        # Set status callbacks on logic instances
        self.logic_a.status_callback = self._on_logic_status_update
        self.logic_b.status_callback = self._on_logic_status_update
        
        logger.info("Execution Manager initialized")
    
    def select_logic(self, logic: str) -> bool:
        """
        Select which logic to use (A or B)
        
        Args:
            logic: "A" or "B"
        
        Returns:
            True if selection successful, False otherwise
        """
        with self._lock:
            logger.info(f"==== Logic Selection Request: {logic.upper()} ====")
            
            # Cannot change logic while one is running
            if self._active_logic != ActiveLogic.NONE:
                logger.warning(f"❌ Cannot select logic - {self._active_logic.value} is currently running")
                logger.warning("⚠️  Stop the active logic first before selecting a new one")
                return False
            
            if logic.upper() == "A":
                self._selected_logic = ActiveLogic.LOGIC_A
                logger.info("✓ Logic A (CG4n51_L1) selected successfully")
                logger.info("  - Standard motor control logic")
                logger.info("  - No RTC date checking")
                logger.info("  - Ready to start")
                self.csv_logger.log_operation("System", "Selection", "LogicA", "Selected")
                return True
            elif logic.upper() == "B":
                self._selected_logic = ActiveLogic.LOGIC_B
                logger.info("✓ Logic B (CG4n51_L2) selected successfully")
                logger.info("  - Motor control with RTC date checking")
                logger.info("  - Target date lockout enabled")
                logger.info("  - Ready to start")
                self.csv_logger.log_operation("System", "Selection", "LogicB", "Selected")
                return True
            else:
                logger.error(f"❌ Invalid logic selection: {logic}")
                logger.error("   Valid options are: 'A' or 'B'")
                return False
    
    def start_selected_logic(self) -> bool:
        """
        Start the currently selected logic
        
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            logger.info("==== Start Logic Request ====")
            
            if self._selected_logic == ActiveLogic.NONE:
                logger.error("❌ Cannot start: No logic selected")
                logger.error("   Please select Logic A or Logic B first")
                return False
            
            if self._active_logic != ActiveLogic.NONE:
                logger.warning(f"⚠️  Cannot start - {self._active_logic.value} is already running")
                logger.warning("   Stop the current logic before starting another")
                return False
            
            try:
                if self._selected_logic == ActiveLogic.LOGIC_A:
                    logger.info("Starting Logic A (CG4n51_L1)...")
                    logger.info("  - Initializing execution thread")
                    self.logic_a.start()
                    self._active_logic = ActiveLogic.LOGIC_A
                    logger.info("✓ Logic A started successfully")
                    logger.info("  - System state: ACTIVE")
                    logger.info("  - Monitoring inputs and executing control logic")
                    return True
                elif self._selected_logic == ActiveLogic.LOGIC_B:
                    logger.info("Starting Logic B (CG4n51_L2)...")
                    logger.info("  - Initializing execution thread")
                    logger.info("  - Checking RTC date")
                    self.logic_b.start()
                    self._active_logic = ActiveLogic.LOGIC_B
                    logger.info("✓ Logic B started successfully")
                    logger.info("  - System state: ACTIVE")
                    logger.info("  - Monitoring inputs, RTC, and executing control logic")
                    return True
            except Exception as e:
                logger.error(f"❌ Failed to start logic: {e}", exc_info=True)
                logger.error("   Check hardware connections and configuration")
                self.csv_logger.log_error("System", "Execution", f"Start failed: {e}")
                return False
        
        return False
    
    def stop_active_logic(self) -> bool:
        """
        Stop the currently active logic
        
        Returns:
            True if stopped successfully, False otherwise
        """
        with self._lock:
            logger.info("==== Stop Logic Request ====")
            
            if self._active_logic == ActiveLogic.NONE:
                logger.warning("⚠️  No logic is currently running")
                logger.info("   System is already idle")
                return False
            
            try:
                if self._active_logic == ActiveLogic.LOGIC_A:
                    logger.info("Stopping Logic A...")
                    logger.info("  - Stopping execution thread")
                    logger.info("  - Halting all motor movements")
                    self.logic_a.stop()
                    logger.info("✓ Logic A stopped successfully")
                    logger.info("  - All motors stopped")
                    logger.info("  - System state: IDLE")
                elif self._active_logic == ActiveLogic.LOGIC_B:
                    logger.info("Stopping Logic B...")
                    logger.info("  - Stopping execution thread")
                    logger.info("  - Halting all motor movements")
                    self.logic_b.stop()
                    logger.info("✓ Logic B stopped successfully")
                    logger.info("  - All motors stopped")
                    logger.info("  - System state: IDLE")
                
                self._active_logic = ActiveLogic.NONE
                return True
            except Exception as e:
                logger.error(f"❌ Failed to stop logic: {e}", exc_info=True)
                logger.error("   Force stopping to ensure safe state")
                self.csv_logger.log_error("System", "Execution", f"Stop failed: {e}")
                self._active_logic = ActiveLogic.NONE
                return False
    
    def emergency_stop_all(self):
        """Emergency stop all operations immediately"""
        logger.critical("""\n
╔═══════════════════════════════════════════╗
║   ⚠️  EMERGENCY STOP TRIGGERED  ⚠️        ║
╚═══════════════════════════════════════════╝
        """)
        logger.critical("🛑 Initiating emergency shutdown sequence")
        logger.critical("   All motor operations will be halted immediately")
        
        with self._lock:
            # Stop both logics
            try:
                logger.critical("  → Stopping Logic A...")
                self.logic_a.stop()
                logger.info("    ✓ Logic A stopped")
            except Exception as e:
                logger.error(f"    ❌ Error stopping Logic A: {e}")
            
            try:
                logger.critical("  → Stopping Logic B...")
                self.logic_b.stop()
                logger.info("    ✓ Logic B stopped")
            except Exception as e:
                logger.error(f"    ❌ Error stopping Logic B: {e}")
            
            self._active_logic = ActiveLogic.NONE
            logger.critical("✓ EMERGENCY STOP COMPLETE")
            logger.critical("   System is now in SAFE STATE")
            logger.critical("   All motors stopped, system idle")
            
            self.csv_logger.log_operation("System", "Emergency", "EmergencyStop", "Completed")
    
    def select_mode(self, mode_number: int) -> bool:
        """
        Select mode (1-5) for active logic
        
        Args:
            mode_number: Mode number (1-5)
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            logger.info(f"==== Mode Selection: Mode {mode_number} ====")
            
            if self._selected_logic == ActiveLogic.NONE:
                logger.error("❌ Cannot select mode: No logic selected")
                logger.error("   Please select Logic A or Logic B first")
                return False
            
            if mode_number < 1 or mode_number > 5:
                logger.error(f"❌ Invalid mode number: {mode_number}")
                logger.error("   Valid modes are: 1, 2, 3, 4, or 5")
                return False
            
            try:
                if self._selected_logic == ActiveLogic.LOGIC_A:
                    logger.info(f"Setting Logic A to Mode {mode_number}")
                    self.logic_a.select_mode(mode_number)
                    logger.info(f"✓ Logic A Mode {mode_number} selected")
                    logger.info(f"   Mode parameters loaded and ready")
                    return True
                elif self._selected_logic == ActiveLogic.LOGIC_B:
                    logger.info(f"Setting Logic B to Mode {mode_number}")
                    self.logic_b.select_mode(mode_number)
                    logger.info(f"✓ Logic B Mode {mode_number} selected")
                    logger.info(f"   Mode parameters loaded and ready")
                    return True
            except Exception as e:
                logger.error(f"❌ Failed to select mode: {e}", exc_info=True)
                logger.error("   Check configuration and try again")
                return False
        
        return False
    
    def enable_manual_mode(self) -> bool:
        """
        Enable manual mode for selected logic
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if self._selected_logic == ActiveLogic.NONE:
                logger.error("No logic selected")
                return False
            
            try:
                if self._selected_logic == ActiveLogic.LOGIC_A:
                    self.logic_a.enable_manual_mode()
                    return True
                elif self._selected_logic == ActiveLogic.LOGIC_B:
                    self.logic_b.enable_manual_mode()
                    return True
            except Exception as e:
                logger.error(f"Failed to enable manual mode: {e}", exc_info=True)
                return False
        
        return False
    
    def disable_manual_mode(self) -> bool:
        """
        Disable manual mode for selected logic
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if self._selected_logic == ActiveLogic.NONE:
                logger.error("No logic selected")
                return False
            
            try:
                if self._selected_logic == ActiveLogic.LOGIC_A:
                    self.logic_a.disable_manual_mode()
                    return True
                elif self._selected_logic == ActiveLogic.LOGIC_B:
                    self.logic_b.disable_manual_mode()
                    return True
            except Exception as e:
                logger.error(f"Failed to disable manual mode: {e}", exc_info=True)
                return False
        
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status
        
        Returns:
            Status dictionary
        """
        with self._lock:
            status = {
                'selected_logic': self._selected_logic.value,
                'active_logic': self._active_logic.value,
                'logic_a_status': self.logic_a.get_status() if self._selected_logic == ActiveLogic.LOGIC_A else None,
                'logic_b_status': self.logic_b.get_status() if self._selected_logic == ActiveLogic.LOGIC_B else None,
            }
            
            # Add RTC info for Logic B
            if self._selected_logic == ActiveLogic.LOGIC_B:
                status['rtc_info'] = self.logic_b.get_rtc_info()
            
            return status
    
    def get_active_logic_status(self) -> Optional[Dict[str, Any]]:
        """
        Get status of currently active logic
        
        Returns:
            Status dictionary or None if no logic active
        """
        with self._lock:
            if self._active_logic == ActiveLogic.LOGIC_A:
                return self.logic_a.get_status()
            elif self._active_logic == ActiveLogic.LOGIC_B:
                return self.logic_b.get_status()
            else:
                return None
    
    def _on_logic_status_update(self, status: Dict[str, Any]):
        """
        Callback for logic status updates
        Forwards to web interface
        
        Args:
            status: Status dictionary from logic
        """
        if self.status_callback:
            # Add execution manager info
            full_status = {
                'selected_logic': self._selected_logic.value,
                'active_logic': self._active_logic.value,
                'logic_status': status
            }
            self.status_callback(full_status)
    
    def update_parameter(self, logic: str, parameter: str, value: Any) -> bool:
        """
        Update configuration parameter for a logic
        
        Args:
            logic: "A" or "B"
            parameter: Parameter path (e.g., "velocidades_lineal.nivel1")
            value: New value
        
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            # Cannot update while logic is running
            if self._active_logic != ActiveLogic.NONE:
                logger.warning("Cannot update parameters while logic is running")
                return False
            
            try:
                # Determine which logic to update
                target_logic = self.logic_a if logic.upper() == "A" else self.logic_b
                
                # Navigate to parameter using dot notation
                config = target_logic.config
                keys = parameter.split('.')
                
                # Get old value for logging
                old_value = config
                for key in keys[:-1]:
                    old_value = old_value[key]
                old_value = old_value[keys[-1]]
                
                # Set new value
                target = config
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                
                # Log the change
                self.csv_logger.log_parameter_change(
                    logic.upper(),
                    parameter,
                    old_value,
                    value,
                    "Engineer",
                    "Parameter updated via web interface"
                )
                
                logger.info(f"Parameter {parameter} updated: {old_value} -> {value}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to update parameter: {e}", exc_info=True)
                self.csv_logger.log_error("System", "Configuration", f"Parameter update failed: {e}")
                return False
    
    def get_configuration(self, logic: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a logic
        
        Args:
            logic: "A" or "B"
        
        Returns:
            Configuration dictionary or None if error
        """
        try:
            if logic.upper() == "A":
                return self.logic_a.config.copy()
            elif logic.upper() == "B":
                return self.logic_b.config.copy()
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to get configuration: {e}")
            return None
    
    def cleanup(self):
        """Cleanup all resources"""
        logger.info("Execution Manager cleanup started")
        
        with self._lock:
            try:
                self.logic_a.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Logic A: {e}")
            
            try:
                self.logic_b.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up Logic B: {e}")
        
        logger.info("Execution Manager cleanup complete")


def create_execution_manager(hw_interface: HardwareInterface,
                            config_a_path: str,
                            config_b_path: str,
                            csv_logger: CSVLogger) -> ExecutionManager:
    """
    Factory function to create Execution Manager
    
    Args:
        hw_interface: Hardware interface instance
        config_a_path: Path to Logic A configuration
        config_b_path: Path to Logic B configuration
        csv_logger: CSV logger instance
    
    Returns:
        ExecutionManager instance
    """
    return ExecutionManager(hw_interface, config_a_path, config_b_path, csv_logger)
