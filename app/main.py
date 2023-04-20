from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello, Pepe!'

@app.route('/dashboard')
def login():
    #return 'Welcome tu login bots'
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run()
