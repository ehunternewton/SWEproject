from flask import Flask, render_template, flash, redirect, url_for, session, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField, DecimalField
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
                # session['username'] = username
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
    cur = mysql.connection.cursor()
    cur.execute("SELECT cr.course_gpa, cr.exam_1, cr.exam_2, cr.final, cd.course_name, c.semester_name, "
                "u.first_name, u.last_name "
                "FROM course_registration cr "
                "INNER JOIN courses c ON cr.course_id = c.id "
                "INNER JOIN course_details cd ON c.course_details_id = cd.id "
                "INNER JOIN users u ON c.teacher_id = u.id "
                "WHERE student_id = %s;", [session['user_id']])
    courses = cur.fetchall()

    return render_template('student_dashboard.html', courses=courses)


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
    cur = mysql.connection.cursor()
    # Get available courses
    cur.execute("SELECT c.id, c.semester_name, cd.course_name FROM courses c " +
                "INNER JOIN course_details cd on c.course_details_id = cd.id " +
                "WHERE teacher_id = %s;", (session['user_id'],))
    courses = cur.fetchall()
    cur.close()
    return render_template('teacher_dashboard.html', courses=courses)


@app.route('/gradebook/<string:course_id>', methods=['GET', 'POST'])
@teacher_logged_in
def gradebook(course_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT cd.course_name, u.first_name, u.last_name, cr.id, cr.course_gpa, cr.exam_1, cr.exam_2, cr.final"
                " FROM course_registration cr "
                "INNER JOIN users u on cr.student_id = u.id "
                "INNER JOIN courses c on cr.course_id = c.id "
                "INNER JOIN course_details cd on c.course_details_id = cd.id "
                "WHERE course_id = %s;", [course_id])
    course = cur.fetchall()
    cur.close()
    return render_template('gradebook.html', course=course)


class UpdateGradesForm(Form):
    exam_1 = DecimalField('Exam 1',  [validators.optional()])
    exam_2 = DecimalField('Exam 2', [validators.optional()])
    final = DecimalField('Final', [validators.optional()])


@app.route('/gradebook/update_grades/<string:course_registration_id>', methods=['GET', 'POST'])
@teacher_logged_in
def update_grades(course_registration_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM course_registration WHERE id = %s;", [course_registration_id])
    result = cur.fetchone()
    cur.close()

    # Get form
    form = UpdateGradesForm(request.form)

    # populate form fields
    form.exam_1.data = result['exam_1']
    form.exam_2.data = result['exam_2']
    form.final.data = result['final']

    if request.method == 'POST' and form.validate():
        exam_1 = request.form['exam_1']
        exam_2 = request.form['exam_2']
        final = request.form['final']
        gpa = 0.0

        if exam_1 != "" and exam_2 != "" and final != "":
            # calculate GPA
            average = (float(exam_1) + float(exam_2) + float(final)) / 3
            if average > 89.5:
                gpa = 4.0
            elif average > 79.5:
                gpa = 3.0
            elif average > 69.5:
                gpa = 2.0
            elif average > 59.5:
                gpa = 1.0
            else:
                gpa = 0.0

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE course_registration SET course_gpa=%s, exam_1=%s, exam_2=%s, final=%s WHERE id=%s",
                    (gpa, exam_1, exam_2, final, course_registration_id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Grades Updated', 'success')

        return redirect(url_for('teacher_dashboard'))

    return render_template('update_grades.html', form=form)


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
    # Get available courses
    cur.execute("SELECT c.id, c.semester_name, cd.course_name, u.first_name, u.last_name " +
                "FROM courses c " +
                "INNER JOIN course_details cd on c.course_details_id = cd.id " +
                "INNER JOIN users u on c.teacher_id = u.id")
    courses = cur.fetchall()
    # Close connection
    cur.close()
    return render_template('admin_dashboard.html', students=students, teachers=teachers, admins=admins,
                           course_details=course_details, courses=courses)


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


# Edit user
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


@app.route('/edit_course/<string:course_id>', methods=['GET', 'POST'])
@admin_logged_in
def edit_course(course_id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM course_details WHERE id = %s", [course_id])
    course = cur.fetchone()
    cur.close()

    form = CourseCreationForm(request.form)
    form.course_name.data = course['course_name']
    form.course_description.data = course['course_description']

    if request.method == 'POST' and form.validate():
        course_name = request.form['course_name']
        course_description = request.form['course_description']

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE course_details SET course_name=%s, course_description=%s WHERE id=%s;",
                    (course_name, course_description,course_id))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Course updated!', 'success')

        return redirect(url_for('admin_dashboard'))

    return render_template('edit_course.html', form=form)


@app.route('/delete_course/<string:course_id>', methods=['POST'])
@admin_logged_in
def delete_course(course_id):
    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM course_details WHERE id = %s", [course_id])

    mysql.connection.commit()
    cur.close()

    flash('Course Deleted', 'success')
    return redirect(url_for('admin_dashboard'))


# Register Form
class CourseRegisterForm(Form):
    course_details_id = StringField('Course Catalog ID', [validators.Length(min=1, max=100)])
    teacher_id = StringField('Teacher ID', [validators.Length(min=1, max=255)])
    semester_name = StringField('Semester', [validators.Length(min=1, max=255)])


@app.route('/course_registration', methods=['GET', 'POST'])
@admin_logged_in
def course_registration():
    form = CourseRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        course_details_id = form.course_details_id.data
        teacher_id = form.teacher_id.data
        semester_name = form.semester_name.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO courses(course_details_id, teacher_id, semester_name) VALUES(%s, %s, %s);",
                    (course_details_id, teacher_id, semester_name))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('Course registered!', 'success')

        return redirect(url_for('admin_dashboard'))

    return render_template('course_registration.html', form=form)


# Register Form
class StudentCourseRegisterForm(Form):
    student_id = StringField('Student ID', [validators.Length(min=1, max=100)])
    course_id = StringField('Course ID', [validators.Length(min=1, max=255)])


@app.route('/student_course_registration', methods=['GET', 'POST'])
@admin_logged_in
def student_course_registration():
    form = StudentCourseRegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        student_id = form.student_id.data
        course_id = form.course_id.data

        # Create cursor
        cur = mysql.connection.cursor()

        # validate student_id is a student and course_id is a course
        cur.execute("SELECT * FROM users WHERE id = %s AND role_id = 3", [student_id])
        student = cur.fetchall()

        cur.execute("SELECT * FROM courses WHERE id = %s", [course_id])
        course = cur.fetchall()

        if len(student) > 0 and len(course) > 0:
            # Execute
            cur.execute("INSERT INTO course_registration(student_id, course_id) VALUES(%s, %s);",
                        (int(student_id), int(course_id)))

            # Commit to DB
            mysql.connection.commit()

            # Close connection
            cur.close()

            flash('Student registered in the course!', 'success')

            return redirect(url_for('admin_dashboard'))
        else:
            error = "StudentID or CourseID does not exist"
            return render_template('student_course_registration.html', form=form, error=error)

    return render_template('student_course_registration.html', form=form)


app.secret_key = 'secret123'
if __name__ == '__main__':
    app.run()
