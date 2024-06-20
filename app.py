from flask import Flask, render_template, request, jsonify
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from io import BytesIO
import base64
from gcode_parser import parse_gcode, extract_movements
from time_calculator import calculate_time, DEFAULT_SETTINGS

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        with open(file_path, 'r') as f:
            gcode = f.read()
        lines = parse_gcode(gcode)
        total_time, time_breakdown = calculate_time(lines, DEFAULT_SETTINGS)
        movements = extract_movements(lines)
        return jsonify({
            'total_time': total_time,
            'time_breakdown': time_breakdown,
            'movements': movements
        })

@app.route('/animation', methods=['POST'])
def animation_endpoint():
    data = request.json
    movements = data['movements']

    fig, ax = plt.subplots()
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)
    line, = ax.plot([], [], lw=2)

    def init():
        line.set_data([], [])
        return line,

    def update(frame):
        xdata, ydata = [], []
        for move in movements[:frame]:
            xdata.extend([move[0][0], move[1][0]])
            ydata.extend([move[0][1], move[1][1]])
        line.set_data(xdata, ydata)
        return line,

    ani = animation.FuncAnimation(fig, update, frames=len(movements), init_func=init, blit=True)

    buf = BytesIO()
    ani.save(buf, format='gif')
    buf.seek(0)
    gif_base64 = base64.b64encode(buf.getvalue()).decode('ascii')

    return jsonify({'animation': gif_base64})

if __name__ == '__main__':
    app.run(debug=True)
