"""
CSV Logger Module
Handles persistent logging of operations, parameters, and errors
"""

import os
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading

logger = logging.getLogger(__name__)


class CSVLogger:
    """Thread-safe CSV logger for system events"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize CSV logger
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self._lock = threading.Lock()
        
        # Initialize log files
        self.operations_log = self._get_log_path("operations")
        self.parameters_log = self._get_log_path("parameters")
        self.errors_log = self._get_log_path("errors")
        
        self._init_operations_log()
        self._init_parameters_log()
        self._init_errors_log()
        
        logger.info(f"CSV Logger initialized in directory: {self.log_dir}")
    
    def _get_log_path(self, log_type: str) -> Path:
        """Get log file path with current date"""
        date_str = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"{log_type}_{date_str}.csv"
    
    def _init_operations_log(self):
        """Initialize operations log with headers if new file"""
        if not self.operations_log.exists():
            with open(self.operations_log, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Logic',
                    'Mode',
                    'Operation',
                    'Status',
                    'Cycle_Count',
                    'Position',
                    'Details'
                ])
            logger.info(f"Created operations log: {self.operations_log}")
    
    def _init_parameters_log(self):
        """Initialize parameters log with headers if new file"""
        if not self.parameters_log.exists():
            with open(self.parameters_log, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Logic',
                    'Parameter',
                    'Old_Value',
                    'New_Value',
                    'Changed_By',
                    'Notes'
                ])
            logger.info(f"Created parameters log: {self.parameters_log}")
    
    def _init_errors_log(self):
        """Initialize errors log with headers if new file"""
        if not self.errors_log.exists():
            with open(self.errors_log, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Timestamp',
                    'Logic',
                    'Error_Type',
                    'Error_Message',
                    'Stack_Trace',
                    'System_State'
                ])
            logger.info(f"Created errors log: {self.errors_log}")
    
    def log_operation(self, logic: str, mode: str, operation: str, 
                     status: str, cycle_count: int = 0, position: str = "",
                     details: str = ""):
        """
        Log an operation event
        
        Args:
            logic: Logic name (A or B)
            mode: Operation mode (Manual/Auto)
            operation: Operation type (Start/Stop/Home/Cycle1/Cycle2/etc.)
            status: Status (Started/Completed/Paused/Stopped/Error)
            cycle_count: Current cycle count
            position: Current position description
            details: Additional details
        """
        with self._lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            try:
                with open(self.operations_log, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        logic,
                        mode,
                        operation,
                        status,
                        cycle_count,
                        position,
                        details
                    ])
            except Exception as e:
                logger.error(f"Failed to write operation log: {e}")
    
    def log_parameter_change(self, logic: str, parameter: str, 
                           old_value: Any, new_value: Any,
                           changed_by: str = "User", notes: str = ""):
        """
        Log a parameter change
        
        Args:
            logic: Logic name (A or B)
            parameter: Parameter name
            old_value: Previous value
            new_value: New value
            changed_by: Who made the change (User/System/Engineer)
            notes: Additional notes
        """
        with self._lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            try:
                with open(self.parameters_log, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        logic,
                        parameter,
                        str(old_value),
                        str(new_value),
                        changed_by,
                        notes
                    ])
                logger.info(f"Parameter change logged: {parameter} = {new_value}")
            except Exception as e:
                logger.error(f"Failed to write parameter log: {e}")
    
    def log_error(self, logic: str, error_type: str, error_message: str,
                 stack_trace: str = "", system_state: str = ""):
        """
        Log an error event
        
        Args:
            logic: Logic name (A or B)
            error_type: Type of error (Hardware/Software/Configuration/Safety)
            error_message: Error message
            stack_trace: Stack trace if available
            system_state: System state at time of error
        """
        with self._lock:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            try:
                with open(self.errors_log, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        timestamp,
                        logic,
                        error_type,
                        error_message,
                        stack_trace,
                        system_state
                    ])
                logger.error(f"Error logged: {error_type} - {error_message}")
            except Exception as e:
                logger.error(f"Failed to write error log: {e}")
    
    def get_recent_operations(self, count: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent operations from log
        
        Args:
            count: Number of recent operations to retrieve
        
        Returns:
            List of operation dictionaries
        """
        operations = []
        
        try:
            with open(self.operations_log, 'r') as f:
                reader = csv.DictReader(f)
                all_ops = list(reader)
                operations = all_ops[-count:] if len(all_ops) > count else all_ops
        except Exception as e:
            logger.error(f"Failed to read operations log: {e}")
        
        return operations
    
    def get_parameter_history(self, parameter: str, logic: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get parameter change history
        
        Args:
            parameter: Parameter name to search for
            logic: Optional logic filter (A or B)
        
        Returns:
            List of parameter change dictionaries
        """
        history = []
        
        try:
            with open(self.parameters_log, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['Parameter'] == parameter:
                        if logic is None or row['Logic'] == logic:
                            history.append(row)
        except Exception as e:
            logger.error(f"Failed to read parameters log: {e}")
        
        return history
    
    def cleanup_old_logs(self, max_age_days: int = 30):
        """
        Clean up log files older than specified days
        
        Args:
            max_age_days: Maximum age of logs to keep
        """
        current_time = datetime.now()
        deleted_count = 0
        
        try:
            for log_file in self.log_dir.glob("*.csv"):
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                age_days = (current_time - file_time).days
                
                if age_days > max_age_days:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file.name} (age: {age_days} days)")
            
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old log files")
        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")


# Global logger instance
_csv_logger: Optional[CSVLogger] = None


def get_csv_logger(log_dir: str = "logs") -> CSVLogger:
    """
    Get global CSV logger instance (singleton pattern)
    
    Args:
        log_dir: Directory for log files
    
    Returns:
        CSVLogger instance
    """
    global _csv_logger
    
    if _csv_logger is None:
        _csv_logger = CSVLogger(log_dir)
    
    return _csv_logger


def init_csv_logger(log_dir: str = "logs") -> CSVLogger:
    """
    Initialize CSV logger (alias for get_csv_logger)
    
    Args:
        log_dir: Directory for log files
    
    Returns:
        CSVLogger instance
    """
    return get_csv_logger(log_dir)
