from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <h1>🦒 Giraffe Kitchen Management</h1>
    <p>השרת עובד בהצלחה!</p>
    <p>Port: 5000</p>
    '''

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)