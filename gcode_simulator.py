import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json

def parse_gcode(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    movements = []
    for line in lines:
        if line.startswith('G'):
            movements.append(line.strip())
    return movements

def simulate(file_path):
    movements = parse_gcode(file_path)
    fig, ax = plt.subplots()
    ax.set_xlim(-200, 200)
    ax.set_ylim(-200, 200)

    xdata, ydata = [], []
    ln, = plt.plot([], [], 'b-', animated=True)

    def init():
        ln.set_data([], [])
        return ln,

    def update(frame):
        cmd = movements[frame]
        if 'X' in cmd and 'Y' in cmd:
            x = float(cmd.split('X')[1].split()[0])
            y = float(cmd.split('Y')[1].split()[0])
            xdata.append(x)
            ydata.append(y)
            ln.set_data(xdata, ydata)
        return ln,

    ani = FuncAnimation(fig, update, frames=range(len(movements)), init_func=init, blit=True)
    plt.close(fig)

    gif_path = file_path.replace('.nc', '.gif')
    ani.save(gif_path, writer='imagemagick')

    total_time = len(movements)  # Simplified for example, replace with actual time calculation

    return {
        'gif_path': gif_path,
        'total_time': total_time
    }

def calculate_cutting_speed(diameter, material):
    # Example calculation, replace with real values
    max_speed = 1000  # Example max speed in RPM
    cutting_speed = (max_speed * diameter * 3.14) / 60  # Calculate cutting speed
    return {
        'cutting_speed': cutting_speed,
        'max_speed': max_speed
    }
