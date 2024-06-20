# gcode_parser.py

import re

def parse_gcode(gcode):
    # Split gcode into lines
    lines = gcode.strip().split('\n')
    return lines

def extract_movements(lines):
    movements = []
    current_position = [0, 0, 0]  # X, Y, Z positions

    for line in lines:
        line = line.strip()
        if line.startswith('G0') or line.startswith('G1') or line.startswith('G2'):
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
            movements.append((current_position, target_position))
            current_position = target_position
    return movements
