"""Standalone Pandas analysis for the sample student marks dataset."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
SUBJECTS = ['python', 'java', 'sql']


def grade(percentage):
    if percentage >= 90:
        return 'A'
    if percentage >= 80:
        return 'B'
    if percentage >= 70:
        return 'C'
    if percentage >= 60:
        return 'D'
    return 'F'


def main():
    df = pd.read_csv(BASE / 'sample_students.csv')
    df['total'] = df[SUBJECTS].sum(axis=1)
    df['average'] = df[SUBJECTS].mean(axis=1).round(2)
    df['percentage'] = (df['total'] / 300 * 100).round(2)
    df['grade'] = df['percentage'].apply(grade)
    df['result'] = df[SUBJECTS].ge(40).all(axis=1).map({True: 'Pass', False: 'Needs Improvement'})

    print('\nSTUDENT PERFORMANCE REPORT')
    print(df[['roll_no', 'name', 'total', 'average', 'percentage', 'grade', 'result']].to_string(index=False))
    print('\nSUBJECT-WISE AVERAGES')
    print(df[SUBJECTS].mean().round(2).to_string())
    topper = df.loc[df['percentage'].idxmax()]
    print(f"\nTOPPER: {topper['name']} ({topper['percentage']}%)")
    print('\nLOW PERFORMERS - BELOW 50%')
    low = df[df['percentage'] < 50]
    print(low[['name', 'percentage']].to_string(index=False) if not low.empty else 'None')

    # Save the calculated report as a CSV file.
    df.to_csv(BASE / 'student_analysis_report.csv', index=False)

    # Draw a subject-average chart.
    averages = df[SUBJECTS].mean()
    averages.plot(kind='bar', title='Average Marks by Subject', ylabel='Average marks', ylim=(0, 100))
    plt.tight_layout()
    plt.savefig(BASE / 'subject_average_chart.png', dpi=140)
    plt.show()


if __name__ == '__main__':
    main()
