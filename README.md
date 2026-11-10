# Student Performance Analysis System

A beginner-friendly web application built with Python, Flask, Pandas, SQLite and Matplotlib.

## Features
- Login and logout with SQLite-backed user authentication
- Dashboard with total students, class average, topper and pass rate
- Add, edit, delete and search student records
- Subject-wise average, highest and lowest marks
- Overall percentage, grade and pass/fail calculation
- Charts for subject averages, student performance and grade distribution
- Export the complete report as CSV

## Run on Windows
1. Install Python 3.10 or newer.
2. Open PowerShell in this project folder.
3. Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
4. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```
5. Start the application:

   ```powershell
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser. Sign in with the demo account below.

## Demo login
- Username: `admin`
- Password: `admin123`

Change this demo password before using the project beyond a local demonstration.

The SQLite database (`students.db`) is created automatically and starts with five sample students. Replace the sample records with your own using **Students → Add Student**.

## Calculation rules
- Total = Python + Java + SQL
- Average = Total / 3
- Percentage = Total / 300 × 100
- Pass = at least 40 marks in every subject
- Grades: A ≥ 90, B ≥ 80, C ≥ 70, D ≥ 60, otherwise F
- Low performer report = overall percentage below 50%

These are demo rules and can be changed in `app.py` to match your college grading policy.

## Run the Pandas analysis separately

```powershell
python analysis.py
```

This reads `sample_students.csv`, calculates each student's total, average, percentage, grade and result, prints the topper and low performers, and saves `student_analysis_report.csv` plus `subject_average_chart.png`.
