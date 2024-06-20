from flask import Flask, render_template, request, jsonify
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import os
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

@app.route('/plot', methods=['POST'])
def plot():
    data = request.json
    movements = data['movements']
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}]])

    # 2D Plot
    for move in movements:
        start, end = move
        fig.add_trace(go.Scatter(x=[start[0], end[0]], y=[start[1], end[1]], mode='lines'), row=1, col=2)

    # 3D Plot
    z_levels = sorted(set(pos[1][2] for pos in movements))
    colors = {'G0': 'red', 'G1': 'green', 'G2': 'blue'}
    for z in z_levels:
        for move in movements:
            start, end = move
            if start[2] == z and end[2] == z:
                g_code = 'G0'
                if abs(start[2] - end[2]) > 0:
                    g_code = 'G1'
                elif abs(start[0] - end[0]) > 0 or abs(start[1] - end[1]) > 0:
                    g_code = 'G2'
                fig.add_trace(go.Scatter3d(x=[start[0], end[0]], y=[start[1], end[1]], z=[start[2], end[2]], mode='lines', line=dict(color=colors[g_code])), row=1, col=1)

    fig.update_layout(height=600, width=1200, title_text="Tool Path Visualization")
    return jsonify(fig.to_plotly_json())

if __name__ == '__main__':
    app.run(debug=True)
