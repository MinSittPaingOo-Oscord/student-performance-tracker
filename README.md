# Student & Instructor Performance Tracker
 
A simple Python (Tkinter) desktop app for tracking assignments, submissions, grades and notes.
The MySQL database is hosted on the cloud (Aiven) and is already set up with sample data (Burmese names).
No database setup is needed.
 
## Features
- Student information (name, academic year/level, email)
- Assignments and exams created by instructors, with due dates and max scores
- Submission status: Not Submitted / Submitted / Late (Late is set automatically when submitting after the due date)
- Grading by the instructor (score + status)
- Notes from both the student and the instructor
## Requirements
- Python 3.9 or newer (with Tkinter, included in the standard Windows installer)
- Internet connection
## Database connection
The connection is already configured inside `app.py`. These details are listed for reference (e.g. to view the data in DBeaver or MySQL Workbench, with SSL set to Require):
 
| Setting  | Value |
|----------|-------|
| Host     | `student-performance-tracker-minsittmandalay137-f4b9.h.aivencloud.com` |
| Port     | `24809` |
| Database | `defaultdb` |
| User     | `avnadmin` |
| Password | `AVNS_P1I1auuEaJWAnyuHu3H` |
 
## How to run
1. Download `app.py` from this repository.
2. Open a terminal in the folder that contains `app.py` and install the one dependency:
```
pip install mysql-connector-python
```
3. Start the app:
```
python app.py
```
   (On Windows, if `pip` or `python` is not recognized, use `py -m pip install mysql-connector-python` and `py app.py`.)
 
## How to test
 
### A. Student view
1. On the login window choose **Role: Student**, pick a name (e.g. **Aung Ko Ko**) and click **Open**.
2. Check the header shows the student's name, year level and email.
3. Check the table lists all assignments/exams with instructor, due date, status and score, and the overall percentage under the table.
4. Click an assignment that is **Not Submitted** (e.g. *Web Page Lab (HTML/CSS)* or *Final Exam*, due in the future):
   - Type a note in **My note** and click **Save note**. The note is saved.
   - Click **Submit work**. The status changes to **Submitted**.
5. Click a graded assignment (e.g. *Midterm Exam*) and check the score and the **Instructor note** are shown.
6. Click **Logout**.
### B. Instructor view
1. Choose **Role: Instructor**, pick a name (e.g. **Daw Khin Mar Lar**) and click **Open**.
2. Check the top table shows only this instructor's assignments.
3. Click **Add assignment**, fill in the title, type, due date (format `YYYY-MM-DD HH:MM`), max score and description, then click **Add**. The new assignment appears in the list.
4. Select an assignment. The bottom table shows every student's status, submission time and score.
5. Select a student, then:
   - Read the **Student note**.
   - Enter a **Score** (it must be between 0 and the max score), choose a **Status** and write an **Instructor note**.
   - Click **Save grade**. The table updates.
6. Click **Delete selected** to remove a test assignment you created.
### C. Check both sides together
1. As an instructor, grade a student's submission and add a note (Step B5).
2. Logout, log in as that student, and confirm the score and instructor note appear.
3. As the student, add a note and submit. Log back in as the instructor and confirm the student note, status and submission time are shown.
## Sample data
- Instructors: Daw Khin Mar Lar, U Tun Tun Oo, Daw Nandar Aye
- Students: Aung Ko Ko, Thiri Htet, Su Myat Noe, Zaw Min Htun, Hnin Ei Phyu, Kyaw Zin Oo, Phyu Phyu Win, Min Thu Ra, Ei Mon Soe, Htet Aung Lin
## Troubleshooting
- **Window opens but the name list is empty / "Database error":** check your internet connection. The cloud database must be running.
- **`ModuleNotFoundError: mysql`:** run `pip install mysql-connector-python` again
