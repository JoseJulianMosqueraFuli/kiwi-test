from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms.fields import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired


app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'secret_key_here'

class LoginForm(FlaskForm):
    username = StringField('Nombre de usuario', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Enviar')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html', error=error)

@app.errorhandler(500)
def no_server(error):
  return render_template('500.html', error=error)  


@app.route('/')
def index():
    return 'Hello, Pepe!'
    

@app.route('/dashboard', methods=['GET', 'POST'])
def login():
    #return 'Welcome tu login bots'
    login_form = LoginForm()

    context = {'login_form': login_form}
    if login_form.validate_on_submit():
        username = login_form.username.data
        session['username'] = username

        flash('Nombre de usario registrado con éxito!')

        return redirect(url_for('index'))
    
    return render_template('dashboard.html', **context)

if __name__ == '__main__':
    app.run()
