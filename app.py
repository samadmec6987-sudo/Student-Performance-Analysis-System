from pathlib import Path
import io
import sqlite3
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session

BASE = Path(__file__).resolve().parent
DB_PATH = BASE / 'students.db'
CHART_DIR = BASE / 'static' / 'charts'
CHART_DIR.mkdir(parents=True, exist_ok=True)
app = Flask(__name__)
app.secret_key = 'student-performance-local-demo-key'
SUBJECTS = ['python', 'java', 'sql']


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.before_request
def require_login():
    allowed = {'login', 'static'}
    if request.endpoint not in allowed and 'user_id' not in session:
        return redirect(url_for('login', next=request.path))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('landing'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        with connect() as con:
            user = con.execute('SELECT id, username, password_hash FROM users WHERE username=?',
                               (username,)).fetchone()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            destination = request.args.get('next', '')
            if not destination.startswith('/') or destination.startswith('//'):
                destination = url_for('landing')
            return redirect(destination)
        flash('Incorrect username or password. Please try again.', 'error')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


def connect():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )''')
        existing_user = con.execute('SELECT id FROM users WHERE username=?', ('admin',)).fetchone()
        if existing_user is None:
            con.execute('INSERT INTO users(username, password_hash) VALUES(?, ?)',
                        ('admin', generate_password_hash('admin123')))
        con.execute('''CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_no TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            python REAL NOT NULL CHECK(python BETWEEN 0 AND 100),
            java REAL NOT NULL CHECK(java BETWEEN 0 AND 100),
            sql REAL NOT NULL CHECK(sql BETWEEN 0 AND 100)
        )''')
        count = con.execute('SELECT COUNT(*) FROM students').fetchone()[0]
        if count == 0:
            demo = [
                ('S001', 'Asha', 85, 90, 80),
                ('S002', 'Ravi', 60, 55, 70),
                ('S003', 'Priya', 95, 92, 98),
                ('S004', 'Kiran', 35, 45, 40),
                ('S005', 'Divya', 75, 82, 88),
            ]
            con.executemany('INSERT INTO students(roll_no,name,python,java,sql) VALUES(?,?,?,?,?)', demo)


def load_data():
    with connect() as con:
        df = pd.read_sql_query('SELECT roll_no, name, python, java, sql FROM students ORDER BY roll_no', con)
    if df.empty:
        return df
    df['Total'] = df[SUBJECTS].sum(axis=1)
    df['Average'] = df[SUBJECTS].mean(axis=1).round(2)
    df['Percentage'] = (df['Total'] / 300 * 100).round(2)
    df['Grade'] = df['Percentage'].apply(get_grade)
    df['Result'] = df[SUBJECTS].ge(40).all(axis=1).map({True: 'Pass', False: 'Needs Improvement'})
    return df


def get_grade(pct):
    if pct >= 90: return 'A'
    if pct >= 80: return 'B'
    if pct >= 70: return 'C'
    if pct >= 60: return 'D'
    return 'F'


def create_charts(df):
    if df.empty:
        return
    # Average marks by subject
    fig, ax = plt.subplots(figsize=(7, 3.6))
    means = df[SUBJECTS].mean()
    means.index = [name.title() for name in means.index]
    bars = ax.bar(means.index, means.values)
    ax.set_title('Average Marks by Subject', fontweight='bold')
    ax.set_ylabel('Average marks')
    ax.set_ylim(0, 100)
    ax.grid(axis='y', alpha=.2)
    for bar, value in zip(bars, means.values):
        ax.text(bar.get_x() + bar.get_width()/2, value + 1, f'{value:.1f}', ha='center', fontsize=9)
    fig.tight_layout(); fig.savefig(CHART_DIR / 'subject_averages.png', dpi=140); plt.close(fig)

    # Student percentage comparison
    fig, ax = plt.subplots(figsize=(8, 3.8))
    ordered = df.sort_values('Percentage', ascending=False)
    bars = ax.bar(ordered['name'], ordered['Percentage'])
    ax.set_title('Overall Student Performance', fontweight='bold')
    ax.set_ylabel('Percentage')
    ax.set_ylim(0, 110)
    ax.grid(axis='y', alpha=.2)
    for bar, value in zip(bars, ordered['Percentage']):
        ax.text(bar.get_x() + bar.get_width()/2, value + 1, f'{value:.1f}%', ha='center', fontsize=8)
    fig.tight_layout(); fig.savefig(CHART_DIR / 'student_performance.png', dpi=140); plt.close(fig)

    # Grade distribution
    fig, ax = plt.subplots(figsize=(6, 3.4))
    grades = df['Grade'].value_counts().reindex(['A','B','C','D','F'], fill_value=0)
    ax.bar(grades.index, grades.values)
    ax.set_title('Grade Distribution', fontweight='bold')
    ax.set_ylabel('Number of students')
    ax.grid(axis='y', alpha=.2)
    fig.tight_layout(); fig.savefig(CHART_DIR / 'grade_distribution.png', dpi=140); plt.close(fig)


@app.route('/')
def landing():
    return render_template('landing.html')


@app.route('/dashboard')
def dashboard():
    df = load_data()
    create_charts(df)
    if df.empty:
        stats = dict(total=0, average=0, topper='—', pass_rate=0, lowest='—')
        topper_record = None
    else:
        top = df.loc[df['Percentage'].idxmax()]
        stats = dict(total=len(df), average=round(df['Percentage'].mean(), 2), topper=top['name'],
                     pass_rate=round((df['Result'] == 'Pass').mean()*100, 1),
                     lowest=df.loc[df['Percentage'].idxmin(), 'name'])
        topper_record = top.to_dict()
    return render_template('dashboard.html', stats=stats, topper=topper_record, recent=df.to_dict('records'))


@app.route('/students')
def students():
    q = request.args.get('q', '').strip().lower()
    df = load_data()
    if q:
        df = df[df['name'].str.lower().str.contains(q) | df['roll_no'].str.lower().str.contains(q)]
    return render_template('students.html', students=df.to_dict('records'), q=q)


@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        try:
            roll = request.form['roll_no'].strip()
            name = request.form['name'].strip()
            marks = [float(request.form[s.lower()]) for s in SUBJECTS]
            if not roll or not name or any(m < 0 or m > 100 for m in marks):
                raise ValueError('Enter a roll number, name, and marks from 0 to 100.')
            with connect() as con:
                con.execute('INSERT INTO students(roll_no,name,python,java,sql) VALUES(?,?,?,?,?)', (roll, name, *marks))
            flash('Student added successfully.', 'success')
            return redirect(url_for('students'))
        except sqlite3.IntegrityError:
            flash('That roll number already exists.', 'error')
        except (ValueError, KeyError):
            flash('Please enter valid details. Marks must be between 0 and 100.', 'error')
    return render_template('student_form.html', student=None)


@app.route('/edit/<roll_no>', methods=['GET', 'POST'])
def edit_student(roll_no):
    with connect() as con:
        student = con.execute('SELECT * FROM students WHERE roll_no=?', (roll_no,)).fetchone()
    if student is None:
        flash('Student not found.', 'error'); return redirect(url_for('students'))
    if request.method == 'POST':
        try:
            marks = [float(request.form[s.lower()]) for s in SUBJECTS]
            name = request.form['name'].strip()
            if not name or any(m < 0 or m > 100 for m in marks): raise ValueError
            with connect() as con:
                con.execute('UPDATE students SET name=?,python=?,java=?,sql=? WHERE roll_no=?', (name, *marks, roll_no))
            flash('Student details updated.', 'success'); return redirect(url_for('students'))
        except (ValueError, KeyError):
            flash('Please enter valid details. Marks must be between 0 and 100.', 'error')
    return render_template('student_form.html', student=dict(student))


@app.post('/delete/<roll_no>')
def delete_student(roll_no):
    with connect() as con:
        con.execute('DELETE FROM students WHERE roll_no=?', (roll_no,))
    flash('Student record deleted.', 'success')
    return redirect(url_for('students'))


@app.route('/analysis')
def analysis():
    df = load_data()
    create_charts(df)
    if df.empty:
        summary = None
        subject_stats = []
        low = []
    else:
        summary = {
            'topper': df.loc[df['Percentage'].idxmax(), 'name'],
            'top_score': df['Percentage'].max(),
            'class_average': round(df['Percentage'].mean(), 2),
            'low_count': int((df['Percentage'] < 50).sum()),
        }
        subject_stats = [{'subject': s.title(), 'average': round(df[s].mean(), 2), 'highest': df[s].max(), 'lowest': df[s].min()} for s in SUBJECTS]
        low = df[df['Percentage'] < 50][['roll_no','name','Percentage']].to_dict('records')
    return render_template('analysis.html', summary=summary, subject_stats=subject_stats, low=low)


@app.route('/export')
def export_csv():
    df = load_data()
    output = io.BytesIO()
    output.write(df.to_csv(index=False).encode('utf-8-sig'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='student_performance_report.csv')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
