from flask import Flask, render_template, request, jsonify
import os
import gcode_simulator

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
        simulation_result = gcode_simulator.simulate(file_path)
        return jsonify(simulation_result)

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/machine_settings')
def machine_settings():
    return render_template('machine_settings.html')

@app.route('/results')
def results():
    return render_template('results.html')

@app.route('/okuma_tutorial')
def okuma_tutorial():
    return render_template('okuma_tutorial.html')

@app.route('/ide')
def ide():
    return render_template('ide.html')

@app.route('/calculate_cutting_speed')
def calculate_cutting_speed():
    diameter = float(request.args.get('diameter'))
    material = request.args.get('material')
    result = gcode_simulator.calculate_cutting_speed(diameter, material)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
