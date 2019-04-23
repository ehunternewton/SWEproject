from flask import session, render_template, redirect, url_for,flash
from functools import wraps
from dao import dao


class student:

    @staticmethod
    def load_routes(app):

        @app.route('/student_dashboard', methods=['GET', 'POST'])
        @student_logged_in
        def student_dashboard():
            response, data = dao.execute(
                "SELECT cr.course_gpa, cr.exam_1, cr.exam_2, cr.final, cd.course_name, c.semester_name, "
                "u.first_name, u.last_name "
                "FROM course_registration cr "
                "INNER JOIN courses c ON cr.course_id = c.id "
                "INNER JOIN course_details cd ON c.course_details_id = cd.id "
                "INNER JOIN users u ON c.teacher_id = u.id "
                "WHERE student_id = %s;", [session['user_id']], 'all')

            response, avg_gpa = dao.execute("SELECT AVG(course_gpa) AS avg_gpa FROM course_registration "
                                            "WHERE student_id = %s;", [session['user_id']], 'all')

            return render_template('student_dashboard.html', courses=data, avg_gpa=avg_gpa)


def student_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'student_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please Login', 'danger')
            return redirect(url_for('student_login'))

    return wrap
