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

    # Create subplots
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'scatter3d'}, {'type': 'scatter'}]])

    # 2D Plot
    for move in movements:
        start, end = move
        fig.add_trace(go.Scatter(x=[start[0], end[0]], y=[start[1], end[1]], mode='lines'), row=1, col=2)

    # 3D Plot
    z_levels = sorted(set(pos[1][2] for pos in movements))
    colors = {'Rapid move': 'red', 'Cutting move': 'green'}
    frames = []
    for i, move in enumerate(movements):
        start, end = move
        g_code = 'Rapid move' if i % 2 == 0 else 'Cutting move'  # Example logic for demonstration
        trace = go.Scatter3d(x=[start[0], end[0]], y=[start[1], end[1]], z=[start[2], end[2]], mode='lines',
                             line=dict(color=colors[g_code]), name=g_code)
        fig.add_trace(trace, row=1, col=1)
        frames.append(go.Frame(data=[trace]))

    fig.frames = frames
    fig.update_layout(height=600, width=1200, title_text="Tool Path Visualization")
    fig.update_layout(updatemenus=[{
        'buttons': [
            {'args': [None, {'frame': {'duration': 500, 'redraw': True}, 'fromcurrent': True}], 'label': 'Play',
             'method': 'animate'},
            {'args': [[None],
                      {'frame': {'duration': 0, 'redraw': True}, 'mode': 'immediate', 'transition': {'duration': 0}}],
             'label': 'Pause', 'method': 'animate'}
        ],
        'direction': 'left',
        'pad': {'r': 10, 't': 87},
        'showactive': False,
        'type': 'buttons',
        'x': 0.1,
        'xanchor': 'right',
        'y': 0,
        'yanchor': 'top'
    }])

    return jsonify(fig.to_plotly_json())


if __name__ == '__main__':
    app.run(debug=True)
