from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)


# Config MySQL
# aws db
app.config['MYSQL_HOST'] = 'xavier.c4dthivni7sx.us-east-1.rds.amazonaws.com'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# local db
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456'
# app.config['MYSQL_DB'] = 'xmendb'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

# init MySQL
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']
            role = data['role_id']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed, set session and redirect to correct dashboard
                session['username'] = username
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
                session['username'] = username
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)
    return render_template('login.html')


def student_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'student_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('student_login'))
    return wrap


@app.route('/student_dashboard', methods=['GET', 'POST'])
@student_logged_in
def student_dashboard():
    return render_template('student_dashboard.html')


def teacher_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'teacher_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('teacher_login'))
    return wrap


@app.route('/teacher_dashboard', methods=['GET', 'POST'])
@teacher_logged_in
def teacher_dashboard():
    return render_template('teacher_dashboard.html')


def admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('admin_login'))
    return wrap


@app.route('/admin_dashboard', methods=['GET', 'POST'])
@admin_logged_in
def admin_dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get students
    cur.execute("SELECT * FROM users WHERE role_id = 3")
    students = cur.fetchall()
    # Get teachers
    cur.execute("SELECT * FROM users WHERE role_id = 2")
    teachers = cur.fetchall()
    # Get admins
    cur.execute("SELECT * FROM users WHERE role_id = 1")
    admins = cur.fetchall()
    # Get course catalog
    cur.execute("SELECT * FROM course_details")
    course_details = cur.fetchall()
    # Close connection
    cur.close()
    return render_template('admin_dashboard.html', students=students, teachers=teachers, admins=admins,
                           course_details=course_details)


# Logout
@app.route('/logout')
#  @is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))


# Register Form
class UserRegisterForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    role = SelectField('Role', choices=[('1', 'Admin'), ('2', 'Teacher'), ('3', 'Student')])
    # password = PasswordField('Password', [
    #     validators.DataRequired(),
    #     validators.EqualTo('confirm', message='Passwords do not match')
    # ])
    # confirm = PasswordField('Confirm Password')


@app.route('/user_registration', methods=['GET', 'POST'])
@admin_logged_in
def user_registration():
    form = UserRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        username = form.username.data
        role = form.role.data
        password = sha256_crypt.encrypt(str('admin'))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO users(first_name, last_name, email, username, password, role_id) VALUES(%s, %s, %s, %s, %s, %s);",
                    (first_name, last_name, email, username, password, role))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('User registered!', 'success')

        redirect(url_for('admin_dashboard'))

    return render_template('user_registration.html', form=form)


# Edit article
@app.route('/edit_user/<string:user_id>', methods=['GET', 'POST'])
@admin_logged_in
def edit_user(user_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM users WHERE id = %s", [user_id])
    user = cur.fetchone()
    cur.close()

    # Get form
    form = UserRegisterForm(request.form)

    # populate article form fields
    form.first_name.data = user['first_name']
    form.last_name.data = user['last_name']
    form.email.data = user['email']
    form.username.data = user['username']
    # role_id is an int, the form requires a string
    form.role.data = str(user['role_id'])

    if request.method == 'POST' and form.validate():
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        username = request.form['username']
        role = request.form['role']

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE users SET first_name=%s, last_name=%s, email=%s, username=%s, role_id=%s WHERE id=%s",
                    (first_name, last_name, email, username, role, user_id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('User Updated', 'success')

        return redirect(url_for('admin_dashboard'))

    return render_template('edit_user.html', form=form)


@app.route('/delete_user/<string:user_id>', methods=['POST'])
@admin_logged_in
def delete_user(user_id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM users WHERE id = %s", [user_id])

    mysql.connection.commit()
    cur.close()

    flash('User Deleted', 'success')
    return redirect(url_for('admin_dashboard'))


# Register Form
class CourseCreationForm(Form):
    course_name = StringField('Course Name', [validators.Length(min=1, max=100)])
    course_description = StringField('Course Description', [validators.Length(min=4, max=255)])


@app.route('/create_course', methods=['GET', 'POST'])
@admin_logged_in
def create_course():
    form = CourseCreationForm(request.form)
    if request.method == 'POST' and form.validate():
        course_name = form.course_name.data
        course_description = form.course_description.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO course_details(course_name, course_description) VALUES(%s, %s);",
                    (course_name, course_description))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Course created!', 'success')

        redirect(url_for('admin_dashboard'))

    return render_template('create_course.html', form=form)


app.secret_key = 'secret123'
if __name__ == '__main__':
    app.run()
