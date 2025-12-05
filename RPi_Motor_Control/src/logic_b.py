"""
Logic B Implementation - CG4n51_L2
Motor control logic with RTC date checking and lockout feature
Translated from Arduino CG4n51_L2.ino
"""

import time
import json
import logging
import threading
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from .logic_a import LogicA, OperationMode, CyclePhase
from .rtc_handler import RTCHandler, create_rtc_handler
from .hardware_interface import HardwareInterface
from .logger import CSVLogger

logger = logging.getLogger(__name__)


class LogicB(LogicA):
    """
    Logic B - CG4n51_L2 implementation
    Extends Logic A with RTC date checking and lockout feature
    """
    
    def __init__(self, hw_interface: HardwareInterface, config_path: str, csv_logger: CSVLogger):
        """
        Initialize Logic B
        
        Args:
            hw_interface: Hardware interface instance
            config_path: Path to configuration JSON file
            csv_logger: CSV logger instance
        """
        # Initialize parent class (Logic A)
        super().__init__(hw_interface, config_path, csv_logger)
        
        # Initialize RTC
        self.rtc = self._init_rtc()
        
        # RTC monitoring
        self._rtc_check_interval = 1.0  # Check RTC every second
        self._last_rtc_check = 0
        self._date_lockout_active = False
        
        logger.info("Logic B initialized with RTC support")
    
    def _init_rtc(self) -> RTCHandler:
        """Initialize RTC handler"""
        rtc_config = self.config.get('rtc_config', {})
        
        if not rtc_config.get('enabled', False):
            logger.warning("RTC is disabled in Logic B configuration")
            return create_rtc_handler(rtc_config, simulate=self.hw.simulate)
        
        rtc = create_rtc_handler(rtc_config, simulate=self.hw.simulate)
        
        # Check RTC validity on startup
        if not rtc.is_valid_date():
            error_msg = "RTC is not returning valid date (year < 2000)"
            logger.error(error_msg)
            self.csv_logger.log_error("B", "Hardware", error_msg, system_state="Initialization")
            
            if not self.hw.simulate:
                logger.critical("RTC validation failed - entering infinite loop (as per Arduino)")
                # In production, this would halt the system
                # For now, we'll just log the error
        
        # Check if target date has been reached
        target = rtc_config.get('target_date', {})
        if self._check_target_date_reached(rtc, target):
            error_msg = f"Target date {target['year']}/{target['month']}/{target['day']} has been reached!"
            logger.critical(error_msg)
            self.csv_logger.log_error("B", "RTC", error_msg, system_state="Lockout")
            self._date_lockout_active = True
            
            if rtc_config.get('lockout_on_target_date', True):
                logger.critical("Date lockout active - system will not operate")
        
        return rtc
    
    def _check_target_date_reached(self, rtc: RTCHandler, target: dict) -> bool:
        """
        Check if target date has been reached
        
        Args:
            rtc: RTC handler instance
            target: Target date dictionary
        
        Returns:
            True if target date reached, False otherwise
        """
        if not target:
            return False
        
        return rtc.check_target_date(
            target.get('year', 2027),
            target.get('month', 10),
            target.get('day', 13)
        )
    
    def _main_loop(self):
        """
        Main execution loop (overrides Logic A)
        Adds RTC monitoring every second
        """
        logger.info("Logic B main loop started")
        
        # Check for date lockout before starting
        if self._date_lockout_active:
            logger.critical("Cannot start - date lockout is active")
            self.csv_logger.log_error("B", "RTC", "Attempted start with active date lockout")
            return
        
        # Initial home finding
        self.encontrar_home()
        
        while self._running:
            try:
                current_time = time.time()
                
                # Periodic RTC check (every second)
                if (current_time - self._last_rtc_check) >= self._rtc_check_interval:
                    self._last_rtc_check = current_time
                    self._check_rtc_status()
                
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
                self.csv_logger.log_error("B", "Software", str(e), system_state=self.mode.value)
        
        logger.info("Logic B main loop ended")
    
    def _check_rtc_status(self):
        """
        Periodic RTC status check
        Logs date/time and checks for target date
        Mimics Arduino's 1-second check in loop()
        """
        try:
            # Read current date/time
            date_str = self.rtc.get_date_string()
            logger.debug(f"RTC: {date_str}")
            
            # Check if target date has been reached
            rtc_config = self.config.get('rtc_config', {})
            target = rtc_config.get('target_date', {})
            
            if self._check_target_date_reached(self.rtc, target):
                if not self._date_lockout_active:
                    error_msg = f"Target date reached! System lockout activated. Date: {date_str}"
                    logger.critical(error_msg)
                    self.csv_logger.log_error("B", "RTC", error_msg, system_state=self.mode.value)
                    self._date_lockout_active = True
                    
                    # Stop all operations
                    self._emergency_stop_due_to_date_lockout()
            
            # Check for invalid date (year < 2000)
            current_dt = self.rtc.read_datetime()
            if current_dt.year < 2000:
                error_msg = f"RTC error: Invalid date {date_str}"
                logger.error(error_msg)
                self.csv_logger.log_error("B", "Hardware", error_msg, system_state=self.mode.value)
                
                if not self.hw.simulate:
                    logger.critical("RTC invalid date - system halting")
                    self._emergency_stop_due_to_rtc_error()
        
        except Exception as e:
            logger.error(f"RTC check failed: {e}")
            self.csv_logger.log_error("B", "Hardware", f"RTC check failed: {e}")
    
    def _emergency_stop_due_to_date_lockout(self):
        """Emergency stop due to target date being reached"""
        logger.critical("EMERGENCY STOP: Date lockout activated")
        
        # Stop all motors
        self.motor_linear.stop()
        self.motor_drill.stop()
        self.nb_linear.disable()
        self.nb_drill.disable()
        
        # Reset all states
        self.en_ejecucion = False
        self.en_espera = False
        self.modo_manual = False
        self.mode = OperationMode.IDLE
        
        # Stop the main loop
        self._running = False
        
        self.csv_logger.log_operation("B", "System", "EmergencyStop", "DateLockout")
    
    def _emergency_stop_due_to_rtc_error(self):
        """Emergency stop due to RTC error"""
        logger.critical("EMERGENCY STOP: RTC error detected")
        
        # Stop all motors
        self.motor_linear.stop()
        self.motor_drill.stop()
        self.nb_linear.disable()
        self.nb_drill.disable()
        
        # Reset all states
        self.en_ejecucion = False
        self.en_espera = False
        self.modo_manual = False
        self.mode = OperationMode.IDLE
        
        # Stop the main loop
        self._running = False
        
        self.csv_logger.log_operation("B", "System", "EmergencyStop", "RTCError")
    
    def start(self):
        """Start logic execution (overrides Logic A to add date check)"""
        # Check for date lockout before starting
        if self._date_lockout_active:
            logger.error("Cannot start Logic B - date lockout is active")
            return
        
        # Check RTC validity
        if not self.rtc.is_valid_date():
            logger.error("Cannot start Logic B - RTC has invalid date")
            return
        
        # Call parent start method
        super().start()
        
        logger.info(f"Logic B started. Current RTC: {self.rtc.get_date_string()}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status (overrides Logic A to add RTC info)"""
        status = super().get_status()
        
        # Add Logic B specific status
        status['logic'] = 'B'
        status['rtc_enabled'] = self.config.get('rtc_config', {}).get('enabled', False)
        status['rtc_datetime'] = self.rtc.get_date_string()
        status['date_lockout_active'] = self._date_lockout_active
        
        # Add target date info
        target = self.config.get('rtc_config', {}).get('target_date', {})
        if target:
            status['target_date'] = f"{target.get('year', 2027)}/{target.get('month', 10)}/{target.get('day', 13)}"
        
        # Add RTC temperature if available
        temp = self.rtc.get_temperature()
        if temp is not None:
            status['rtc_temperature_c'] = round(temp, 2)
        
        return status
    
    def get_rtc_info(self) -> Dict[str, Any]:
        """
        Get detailed RTC information
        
        Returns:
            Dictionary with RTC details
        """
        try:
            current_dt = self.rtc.read_datetime()
            target = self.config.get('rtc_config', {}).get('target_date', {})
            
            return {
                'current_datetime': self.rtc.get_date_string(),
                'current_year': current_dt.year,
                'current_month': current_dt.month,
                'current_day': current_dt.day,
                'target_year': target.get('year', 2027),
                'target_month': target.get('month', 10),
                'target_day': target.get('day', 13),
                'days_until_target': (datetime(target.get('year', 2027), 
                                              target.get('month', 10), 
                                              target.get('day', 13)) - current_dt).days,
                'date_lockout_active': self._date_lockout_active,
                'date_valid': self.rtc.is_valid_date(),
                'temperature_c': self.rtc.get_temperature(),
                'simulated': self.rtc.simulate
            }
        except Exception as e:
            logger.error(f"Failed to get RTC info: {e}")
            return {'error': str(e)}
    
    def set_rtc_datetime(self, year: int, month: int, day: int, 
                        hour: int = 0, minute: int = 0, second: int = 0):
        """
        Set RTC date/time (engineer function)
        
        Args:
            year: Year (2000-2099)
            month: Month (1-12)
            day: Day (1-31)
            hour: Hour (0-23)
            minute: Minute (0-59)
            second: Second (0-59)
        """
        try:
            dt = datetime(year, month, day, hour, minute, second)
            self.rtc.set_datetime(dt)
            
            self.csv_logger.log_parameter_change(
                "B",
                "RTC_DateTime",
                self.rtc.get_date_string(),
                dt.strftime("%Y/%m/%d %H:%M:%S"),
                "Engineer",
                "RTC date/time manually set"
            )
            
            logger.info(f"RTC set to: {dt}")
            
            # Re-check date lockout status
            target = self.config.get('rtc_config', {}).get('target_date', {})
            if self._check_target_date_reached(self.rtc, target):
                self._date_lockout_active = True
                logger.warning("Date lockout activated after RTC update")
            else:
                self._date_lockout_active = False
                logger.info("Date lockout cleared after RTC update")
            
        except Exception as e:
            logger.error(f"Failed to set RTC: {e}")
            self.csv_logger.log_error("B", "Configuration", f"RTC set failed: {e}")
    
    def cleanup(self):
        """Cleanup resources (overrides Logic A)"""
        super().cleanup()
        logger.info("Logic B cleanup complete")


def create_logic_b(hw_interface: HardwareInterface, config_path: str, 
                   csv_logger: CSVLogger) -> LogicB:
    """
    Factory function to create Logic B instance
    
    Args:
        hw_interface: Hardware interface instance
        config_path: Path to configuration JSON file
        csv_logger: CSV logger instance
    
    Returns:
        LogicB instance
    """
    return LogicB(hw_interface, config_path, csv_logger)
