import math
import re

# Define default constants for machine parameters
DEFAULT_SETTINGS = {
    "RAPID_SPEED": 5000,  # Rapid move speed in mm/min
    "MAX_FEED_RATE": 1000,  # Maximum feed rate in mm/min
    "ACCELERATION": 2000,  # Acceleration in mm/s^2
    "PALLET_CHANGE_TIME": 20,  # Pallet change time in seconds
    "M143_TIME": 1,  # Spindle speed control time
    "M142_TIME": 2,  # Spindle stop and optional stop time
    "M9_TIME": 1,  # Coolant off time
    "M05_TIME": 1  # Spindle stop time
}

def calculate_time(lines, settings=DEFAULT_SETTINGS):
    total_time = 0.0
    current_feed_rate = settings['MAX_FEED_RATE']
    current_position = [0, 0, 0]  # X, Y, Z positions
    time_breakdown = {
        "Rapid move": 0.0,
        "Cutting move": 0.0,
        "Pallet change": 0.0,
        "Spindle speed control": 0.0,
        "Spindle stop and optional stop": 0.0,
        "Coolant off": 0.0,
        "Spindle stop": 0.0
    }

    for line in lines:
        line = line.strip()
        if line.startswith('G0') or line.startswith('G1'):
            match = re.findall(r'[XYZ]-?\d+\.?\d*', line)
            target_position = current_position.copy()
            for m in match:
                axis = m[0]
                value = float(m[1:])
                if axis == 'X':
                    target_position[0] = value
                elif axis == 'Y':
                    target_position[1] = value
                elif axis == 'Z':
                    target_position[2] = value

            distance = math.sqrt(
                (target_position[0] - current_position[0]) ** 2 +
                (target_position[1] - current_position[1]) ** 2 +
                (target_position[2] - current_position[2]) ** 2
            )

            if line.startswith('G0'):
                speed = settings['RAPID_SPEED']
                move_type = 'Rapid move'
            else:
                feed_match = re.search(r'F\d+\.?\d*', line)
                if feed_match:
                    current_feed_rate = float(feed_match.group()[1:])
                speed = current_feed_rate
                move_type = 'Cutting move'

            # Time to accelerate to the speed
            accel_time = speed / (settings['ACCELERATION'] * 60)
            accel_distance = 0.5 * (speed / 60) * accel_time

            if distance <= 2 * accel_distance:
                # Not enough distance to reach full speed
                move_time = 2 * math.sqrt(distance / (settings['ACCELERATION'] * 60))
            else:
                # Time to travel the acceleration phase + constant speed phase + deceleration phase
                move_time = 2 * accel_time + (distance - 2 * accel_distance) / (speed / 60)

            total_time += move_time
            time_breakdown[move_type] += move_time
            current_position = target_position

        elif line.startswith('M'):
            if 'M60' in line:
                total_time += settings['PALLET_CHANGE_TIME']
                time_breakdown["Pallet change"] += settings['PALLET_CHANGE_TIME']
            elif 'M143' in line:
                total_time += settings['M143_TIME']
                time_breakdown["Spindle speed control"] += settings['M143_TIME']
            elif 'M142' in line:
                total_time += settings['M142_TIME']
                time_breakdown["Spindle stop and optional stop"] += settings['M142_TIME']
            elif 'M9' in line:
                total_time += settings['M9_TIME']
                time_breakdown["Coolant off"] += settings['M9_TIME']
            elif 'M05' in line:
                total_time += settings['M05_TIME']
                time_breakdown["Spindle stop"] += settings['M05_TIME']

    return total_time, time_breakdown
