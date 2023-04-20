from flask import Flask, render_template
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap(app)

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error)

@app.errorhandler(500)
def no_server(error):
  return render_template('500.html', error=error)  


@app.route('/')
def index():
    return 'Hello, Pepe!'

@app.route('/dashboard')
def login():
    #return 'Welcome tu login bots'
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run()
