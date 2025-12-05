"""
RTC Handler Module
Interface for DS3231 Real-Time Clock module
Handles date/time checking for Logic B lockout feature
"""

import logging
from datetime import datetime
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)


class RTCHandler:
    """DS3231 RTC interface handler"""
    
    def __init__(self, i2c_bus: int = 1, i2c_address: int = 0x68, simulate: bool = False):
        """
        Initialize RTC handler
        
        Args:
            i2c_bus: I2C bus number (usually 1 on RPi)
            i2c_address: I2C address of DS3231 (default 0x68)
            simulate: Use simulated RTC (system time)
        """
        self.i2c_bus = i2c_bus
        self.i2c_address = i2c_address
        self.simulate = simulate
        self.rtc = None
        
        if not simulate:
            self._init_real_rtc()
        else:
            logger.info("RTC Handler initialized (SIMULATED - using system time)")
    
    def _init_real_rtc(self):
        """Initialize real DS3231 RTC module"""
        try:
            import smbus2
            self.bus = smbus2.SMBus(self.i2c_bus)
            
            # Try to read from RTC to verify connection
            try:
                self.bus.read_byte_data(self.i2c_address, 0x00)
                logger.info(f"DS3231 RTC found at I2C address {hex(self.i2c_address)}")
                
                # Check if RTC lost power
                if self._check_oscillator_stopped():
                    logger.warning("RTC oscillator was stopped (power loss detected)")
                    self._clear_oscillator_stop_flag()
                    logger.info("RTC oscillator stop flag cleared")
                
            except Exception as e:
                logger.error(f"DS3231 RTC not responding at {hex(self.i2c_address)}: {e}")
                logger.warning("Falling back to SIMULATED RTC (system time)")
                self.simulate = True
                
        except ImportError:
            logger.error("smbus2 not installed. Install with: pip install smbus2")
            logger.warning("Falling back to SIMULATED RTC (system time)")
            self.simulate = True
        except Exception as e:
            logger.error(f"Failed to initialize I2C bus: {e}")
            logger.warning("Falling back to SIMULATED RTC (system time)")
            self.simulate = True
    
    def _bcd_to_decimal(self, bcd: int) -> int:
        """Convert BCD (Binary Coded Decimal) to decimal"""
        return ((bcd >> 4) * 10) + (bcd & 0x0F)
    
    def _decimal_to_bcd(self, decimal: int) -> int:
        """Convert decimal to BCD"""
        return ((decimal // 10) << 4) | (decimal % 10)
    
    def _check_oscillator_stopped(self) -> bool:
        """Check if oscillator stop flag is set (indicates power loss)"""
        if self.simulate:
            return False
        
        try:
            status = self.bus.read_byte_data(self.i2c_address, 0x0F)
            return bool(status & 0x80)  # Check OSF bit
        except:
            return False
    
    def _clear_oscillator_stop_flag(self):
        """Clear oscillator stop flag"""
        if self.simulate:
            return
        
        try:
            status = self.bus.read_byte_data(self.i2c_address, 0x0F)
            status &= ~0x80  # Clear OSF bit
            self.bus.write_byte_data(self.i2c_address, 0x0F, status)
        except Exception as e:
            logger.error(f"Failed to clear OSF flag: {e}")
    
    def read_datetime(self) -> datetime:
        """
        Read current date/time from RTC
        
        Returns:
            datetime object with current date/time
        """
        if self.simulate:
            return datetime.now()
        
        try:
            # Read time registers (0x00-0x06)
            data = []
            for reg in range(0x00, 0x07):
                data.append(self.bus.read_byte_data(self.i2c_address, reg))
            
            # Parse BCD data
            second = self._bcd_to_decimal(data[0] & 0x7F)
            minute = self._bcd_to_decimal(data[1] & 0x7F)
            hour = self._bcd_to_decimal(data[2] & 0x3F)  # 24-hour format
            # data[3] is day of week, skip it
            day = self._bcd_to_decimal(data[4] & 0x3F)
            month = self._bcd_to_decimal(data[5] & 0x1F)
            year = self._bcd_to_decimal(data[6]) + 2000
            
            return datetime(year, month, day, hour, minute, second)
            
        except Exception as e:
            logger.error(f"Failed to read from RTC: {e}")
            logger.warning("Falling back to system time")
            return datetime.now()
    
    def set_datetime(self, dt: datetime):
        """
        Set RTC date/time
        
        Args:
            dt: datetime object to set
        """
        if self.simulate:
            logger.info(f"[SIMULATED] Would set RTC to: {dt}")
            return
        
        try:
            # Convert to BCD and write to registers
            self.bus.write_byte_data(self.i2c_address, 0x00, self._decimal_to_bcd(dt.second))
            self.bus.write_byte_data(self.i2c_address, 0x01, self._decimal_to_bcd(dt.minute))
            self.bus.write_byte_data(self.i2c_address, 0x02, self._decimal_to_bcd(dt.hour))
            # Skip day of week (0x03)
            self.bus.write_byte_data(self.i2c_address, 0x04, self._decimal_to_bcd(dt.day))
            self.bus.write_byte_data(self.i2c_address, 0x05, self._decimal_to_bcd(dt.month))
            self.bus.write_byte_data(self.i2c_address, 0x06, self._decimal_to_bcd(dt.year - 2000))
            
            logger.info(f"RTC set to: {dt}")
            
        except Exception as e:
            logger.error(f"Failed to set RTC: {e}")
    
    def check_target_date(self, target_year: int, target_month: int, target_day: int) -> bool:
        """
        Check if current date has reached or passed target date
        
        Args:
            target_year: Target year
            target_month: Target month (1-12)
            target_day: Target day (1-31)
        
        Returns:
            True if current date >= target date, False otherwise
        """
        current = self.read_datetime()
        target = datetime(target_year, target_month, target_day)
        
        has_reached = current >= target
        
        if has_reached:
            logger.warning(f"Target date reached! Current: {current.date()}, Target: {target.date()}")
        
        return has_reached
    
    def is_valid_date(self) -> bool:
        """
        Check if RTC is returning valid date (not stuck in year < 2000)
        
        Returns:
            True if date is valid, False otherwise
        """
        current = self.read_datetime()
        is_valid = current.year >= 2000
        
        if not is_valid:
            logger.error(f"RTC returning invalid date: {current}")
        
        return is_valid
    
    def get_date_string(self) -> str:
        """
        Get formatted date/time string
        
        Returns:
            Formatted string "YYYY/MM/DD HH:MM:SS"
        """
        dt = self.read_datetime()
        return dt.strftime("%Y/%m/%d %H:%M:%S")
    
    def get_temperature(self) -> Optional[float]:
        """
        Read temperature from DS3231 (has built-in temperature sensor)
        
        Returns:
            Temperature in Celsius, or None if error
        """
        if self.simulate:
            return None
        
        try:
            # Read temperature registers (0x11-0x12)
            msb = self.bus.read_byte_data(self.i2c_address, 0x11)
            lsb = self.bus.read_byte_data(self.i2c_address, 0x12)
            
            # Convert to temperature
            temp = msb + (lsb >> 6) * 0.25
            
            # Handle negative temperatures
            if msb & 0x80:
                temp = temp - 256
            
            return temp
            
        except Exception as e:
            logger.error(f"Failed to read temperature: {e}")
            return None


def create_rtc_handler(config: dict, simulate: bool = False) -> RTCHandler:
    """
    Factory function to create RTC handler from configuration
    
    Args:
        config: RTC configuration dictionary
        simulate: Force simulation mode
    
    Returns:
        RTCHandler instance
    """
    if not config.get('enabled', False):
        logger.info("RTC disabled in configuration, using simulated mode")
        return RTCHandler(simulate=True)
    
    i2c_bus = config.get('i2c_bus', 1)
    i2c_address = int(config.get('i2c_address', '0x68'), 16)
    
    return RTCHandler(i2c_bus=i2c_bus, i2c_address=i2c_address, simulate=simulate)
