from flask import Flask, render_template, flash, redirect, url_for, session, request
from passlib.hash import sha256_crypt
from dao import dao
from admin_user import admin
from student_user import student
from teacher_user import teacher

app = Flask(__name__)
# init MySQL
mysql = dao.connect_db(app)

student.load_routes(app)
teacher.load_routes(app)
admin.load_routes(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Get user by username
        response, data = dao.execute("SELECT * FROM users WHERE username = %s", [username],'one')

        if response > 0:
            # Get stored hash
            password = data['password']
            role = data['role_id']
            user_id = data['id']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed, set session and redirect to correct dashboard
                session['username'] = username
                session['user_id'] = user_id
                if role == 1:
                    session['admin_logged_in'] = True
                    flash('You are now logged in', 'success')
                    return redirect(url_for('admin_dashboard'))
                elif role == 2:
                    session['teacher_logged_in'] = True
                    flash('You are now logged in', 'success')
                    return redirect(url_for('teacher_dashboard'))
                elif role == 3:
                    session['student_logged_in'] = True
                    flash('You are now logged in', 'success')
                    return redirect(url_for('student_dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


# Logout
@app.route('/logout')
#  @is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


app.secret_key = 'secret123'
if __name__ == '__main__':
    app.run()
