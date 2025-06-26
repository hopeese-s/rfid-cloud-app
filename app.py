from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
import csv
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, async_mode='eventlet')

# เก็บ log ล่าสุด 10 รายการ
scan_log = []

def load_lookup_table():
    lookup = {}
    try:
        with open('rfid_lookup.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                lookup[row['UID']] = {
                    'registration': row['registration'],
                    'name': row['name'],
                    'sex': row['sex']
                }
    except FileNotFoundError:
        print("CSV file not found. Using empty lookup table.")
    return lookup

lookup_table = load_lookup_table()

@app.route('/')
def index():
    return render_template('index.html', scan_log=scan_log)

@socketio.on('connect')
def handle_connect():
    emit('update_log', scan_log)

@app.route('/scan', methods=['POST'])
def handle_scan():
    uid = request.form.get('uid')
    if uid in lookup_table:
        entry = {
            'name': lookup_table[uid]['name'],
            'sex': lookup_table[uid]['sex'],
            'registration': lookup_table[uid]['registration']
        }
    else:
        entry = {'name': 'Unknown', 'sex': '-', 'registration': '-'}
    
    scan_log.insert(0, entry)
    if len(scan_log) > 10:
        scan_log.pop()
    
    # Broadcast to all clients
    socketio.emit('new_scan', entry)
    return ('', 204)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
