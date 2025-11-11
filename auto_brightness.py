import requests
import time
import subprocess
import logging
import signal
import sys
from pathlib import Path

# ===== CONFIGURATION =====
HOME_ASSISTANT_URL = "http://home.local:8123"
API_TOKEN = "api_key"
LUX_SENSOR_ENTITY_ID = "sensor.lux_values"
LUX_HYSTERESIS_THRESHOLD = 3.0  # Minimum lux change required to update brightness


# ===== Display Outputs =====
DISPLAY_OUTPUTS = ["HDMI-1", "HDMI-2"]  # Replace with your actual output names

# ===== Brightness Mapping =====
LUX_BRIGHTNESS_MAPPING = [
    (1, 0), (10, 25), (50, 35), (200, 50), (500, 70), (1000, 100)
]
# Setup logging to file for background operation
log_file = Path.home() / ".auto_brightness.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)  # Remove this line for complete silence
    ]
)

# Global variables
previous_lux = None
previous_brightness = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logging.info("Received shutdown signal, exiting...")
    sys.exit(0)

def set_monitor_brightness(brightness_percentage):
    """Set brightness on all specified displays using kscreen-doctor."""
    global previous_brightness
    
    brightness_value = max(0, min(100, int(round(brightness_percentage))))
    
    if previous_brightness is not None and brightness_value == previous_brightness:
        return True
    
    success_count = 0
    for output in DISPLAY_OUTPUTS:
        if set_display_brightness(output, brightness_value):
            success_count += 1
    
    if success_count > 0:
        logging.info(f"Set brightness to {brightness_value}% on {success_count} displays")
        previous_brightness = brightness_value
        return True
    
    logging.error("Failed to set brightness on any displays")
    return False

def set_display_brightness(output_name, brightness_value):
    """Set brightness on a specific display output."""
    try:
        result = subprocess.run([
            "kscreen-doctor", f"output.{output_name}.brightness.{brightness_value}"
        ], capture_output=True, text=True, timeout=5)
        
        return result.returncode == 0
            
    except Exception:
        return False

def get_lux_from_home_assistant():
    """Fetch lux value from Home Assistant."""
    url = f"{HOME_ASSISTANT_URL}/api/states/{LUX_SENSOR_ENTITY_ID}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return float(response.json()['state'])
    except Exception:
        return None

def map_lux_to_brightness(lux_value):
    """Map lux to brightness percentage."""
    calibration_points = sorted(LUX_BRIGHTNESS_MAPPING, key=lambda x: x[0])
    
    if lux_value <= calibration_points[0][0]:
        return float(calibration_points[0][1])
    if lux_value >= calibration_points[-1][0]:
        return float(calibration_points[-1][1])
    
    for i in range(len(calibration_points) - 1):
        lux_low, brightness_low = calibration_points[i]
        lux_high, brightness_high = calibration_points[i + 1]
        if lux_low <= lux_value <= lux_high:
            ratio = (lux_value - lux_low) / (lux_high - lux_low)
            interpolated = brightness_low + ratio * (brightness_high - brightness_low)
            return round(interpolated, 1)
    
    return float(calibration_points[-1][1])

def should_update_brightness(current_lux, current_brightness):
    """Check if brightness should be updated."""
    global previous_lux
    
    if previous_lux is None:
        return True
    
    lux_difference = abs(current_lux - previous_lux)
    return lux_difference >= LUX_HYSTERESIS_THRESHOLD

def main():
    global previous_lux, previous_brightness
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logging.info("Starting Auto Brightness Control (Background)")
    logging.info(f"Controlling displays: {DISPLAY_OUTPUTS}")
    
    try:
        while True:
            current_lux = get_lux_from_home_assistant()
            
            if current_lux is not None:
                new_brightness = map_lux_to_brightness(current_lux)
                
                if should_update_brightness(current_lux, new_brightness):
                    logging.info(f"Update: {current_lux} lux -> {new_brightness}%")
                    set_monitor_brightness(new_brightness)
                    previous_lux = current_lux
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        logging.info("Script stopped by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
