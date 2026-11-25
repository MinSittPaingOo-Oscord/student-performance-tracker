
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

import mysql.connector

DB = dict(
    host="student-performance-tracker-minsittmandalay137-f4b9.h.aivencloud.com",
    port=24809,
    user="avnadmin",
    password="AVNS_P1I1auuEaJWAnyuHu3H",
    database="defaultdb",
)

USE_SSL = os.getenv("DB_SSL", "true").lower() == "true"  # most cloud DBs require SSL
SSL_CA = os.getenv("DB_SSL_CA", "")  # optional: path to the provider's CA certificate (ca.pem)

STATUSES = ["Not Submitted", "Submitted", "Late"]
FMT = "%Y-%m-%d %H:%M"

def run(sql, params=(), write=False):
    """Run one query. Returns rows (read) or lastrowid (write)."""
    extra = {"ssl_ca": SSL_CA} if (USE_SSL and SSL_CA) else {}
    c = mysql.connector.connect(**DB, ssl_disabled=not USE_SSL, connection_timeout=15, **extra)
    try:
        cur = c.cursor(dictionary=True)
        cur.execute(sql, params)
        if write:
            c.commit()
            return cur.lastrowid
        return cur.fetchall()
    finally:
        c.close()

def tree(parent, cols, widths, height=7):
    t = ttk.Treeview(parent, columns=[c[0] for c in cols], show="headings", height=height)
    for (key, label), w in zip(cols, widths):
        t.heading(key, text=label)
        t.column(key, width=w, anchor="w")
    sb = ttk.Scrollbar(parent, orient="vertical", command=t.yview)
    t.configure(yscrollcommand=sb.set)
    t.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    return t


def set_text(widget, value, readonly=False):
    widget.config(state="normal")
    widget.delete("1.0", "end")
    widget.insert("1.0", value or "")
    if readonly:
        widget.config(state="disabled")


def dt(v):
    return v.strftime(FMT) if v else ""


def safe(fn):
    """Show DB errors in a message box instead of crashing."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except mysql.connector.Error as e:
            messagebox.showerror("Database error", str(e))
    return wrapper


class InstructorWin(tk.Toplevel):
    def __init__(self, login, user):
        super().__init__(login)
        self.login, self.user = login, user
        self.title(f"Instructor - {user['name']}")
        self.geometry("900x680")
        self.protocol("WM_DELETE_WINDOW", login.destroy)

        ttk.Label(self, text=f"Instructor: {user['name']}", font=("", 13, "bold")).pack(pady=6)

        f1 = ttk.LabelFrame(self, text="My assignments / exams")
        f1.pack(fill="both", expand=True, padx=8, pady=4)
        box = ttk.Frame(f1); box.pack(fill="both", expand=True)
        self.at = tree(box, [("id", "ID"), ("title", "Title"), ("type", "Type"),
                             ("due", "Due date"), ("max", "Max")], [40, 330, 90, 150, 60], 6)
        self.at.bind("<<TreeviewSelect>>", lambda e: self.load_subs())
        bar = ttk.Frame(f1); bar.pack(fill="x", pady=3)
        ttk.Button(bar, text="Add assignment", command=self.add_dialog).pack(side="left", padx=4)
        ttk.Button(bar, text="Delete selected", command=self.delete_assignment).pack(side="left")
        ttk.Button(bar, text="Logout", command=self.logout).pack(side="right", padx=4)

        f2 = ttk.LabelFrame(self, text="Submissions & grading")
        f2.pack(fill="both", expand=True, padx=8, pady=4)
        box2 = ttk.Frame(f2); box2.pack(fill="both", expand=True)
        self.st = tree(box2, [("student", "Student"), ("year", "Year"), ("status", "Status"),
                              ("at", "Submitted at"), ("score", "Score")],
                       [200, 80, 110, 150, 70], 7)
        self.st.bind("<<TreeviewSelect>>", lambda e: self.fill_form())

        g = ttk.Frame(f2); g.pack(fill="x", padx=4, pady=4)
        ttk.Label(g, text="Student note:").grid(row=0, column=0, sticky="nw")
        self.t_student = tk.Text(g, height=3, width=40, state="disabled", bg="#f0f0f0")
        self.t_student.grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(g, text="Instructor note:").grid(row=0, column=2, sticky="nw")
        self.t_inst = tk.Text(g, height=3, width=40)
        self.t_inst.grid(row=0, column=3, padx=4, pady=2)
        ttk.Label(g, text="Score:").grid(row=1, column=0, sticky="e")
        self.e_score = ttk.Entry(g, width=10)
        self.e_score.grid(row=1, column=1, sticky="w", padx=4)
        ttk.Label(g, text="Status:").grid(row=1, column=2, sticky="e")
        self.c_status = ttk.Combobox(g, values=STATUSES, state="readonly", width=15)
        self.c_status.grid(row=1, column=3, sticky="w", padx=4)
        ttk.Button(g, text="Save grade", command=self.save).grid(row=2, column=3, sticky="e", pady=4)

        self.load_assignments()

    def logout(self):
        self.destroy()
        self.login.deiconify()

    @safe
    def load_assignments(self):
        self.at.delete(*self.at.get_children())
        for r in run("SELECT * FROM assignments WHERE instructor_id=%s ORDER BY due_date",
                     (self.user["id"],)):
            self.at.insert("", "end", iid=str(r["id"]),
                           values=(r["id"], r["title"], r["type"], dt(r["due_date"]), r["max_score"]))
        self.st.delete(*self.st.get_children())

    def sel_assignment(self):
        s = self.at.selection()
        return int(s[0]) if s else None

    @safe
    def load_subs(self):
        aid = self.sel_assignment()
        self.st.delete(*self.st.get_children())
        if not aid:
            return
        rows = run("""SELECT s.id, st.name, st.year_level, s.status, s.submitted_at, s.score
                      FROM submissions s JOIN students st ON st.id=s.student_id
                      WHERE s.assignment_id=%s ORDER BY st.name""", (aid,))
        for r in rows:
            self.st.insert("", "end", iid=str(r["id"]),
                           values=(r["name"], r["year_level"], r["status"], dt(r["submitted_at"]),
                                   "" if r["score"] is None else r["score"]))

    @safe
    def fill_form(self):
        s = self.st.selection()
        if not s:
            return
        r = run("SELECT * FROM submissions WHERE id=%s", (int(s[0]),))[0]
        set_text(self.t_student, r["student_note"], readonly=True)
        set_text(self.t_inst, r["instructor_note"])
        self.e_score.delete(0, "end")
        self.e_score.insert(0, "" if r["score"] is None else str(r["score"]))
        self.c_status.set(r["status"])

    @safe
    def save(self):
        s, aid = self.st.selection(), self.sel_assignment()
        if not s:
            return messagebox.showinfo("Select", "Select a student submission first.")
        mx = run("SELECT max_score FROM assignments WHERE id=%s", (aid,))[0]["max_score"]
        raw = self.e_score.get().strip()
        score = None
        if raw:
            try:
                score = float(raw)
            except ValueError:
                return messagebox.showerror("Error", "Score must be a number.")
            if not 0 <= score <= mx:
                return messagebox.showerror("Error", f"Score must be between 0 and {mx}.")
        run("UPDATE submissions SET score=%s, status=%s, instructor_note=%s WHERE id=%s",
            (score, self.c_status.get(), self.t_inst.get("1.0", "end").strip(), int(s[0])), write=True)
        self.load_subs()
        messagebox.showinfo("Saved", "Grade saved.")

    def add_dialog(self):
        d = tk.Toplevel(self); d.title("Add assignment"); d.grab_set()
        labels = ["Title", "Type", "Due (YYYY-MM-DD HH:MM)", "Max score", "Description"]
        for i, l in enumerate(labels):
            ttk.Label(d, text=l).grid(row=i, column=0, sticky="w", padx=6, pady=4)
        e_title = ttk.Entry(d, width=40)
        c_type = ttk.Combobox(d, values=["Assignment", "Exam"], state="readonly"); c_type.set("Assignment")
        e_due = ttk.Entry(d, width=40)
        e_due.insert(0, (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d 23:59"))
        e_max = ttk.Entry(d, width=10); e_max.insert(0, "100")
        t_desc = tk.Text(d, height=4, width=40)
        for i, w in enumerate([e_title, c_type, e_due, e_max, t_desc]):
            w.grid(row=i, column=1, padx=6, pady=4, sticky="w")

        @safe
        def ok():
            try:
                due = datetime.strptime(e_due.get().strip(), FMT)
                mx = int(e_max.get())
            except ValueError:
                return messagebox.showerror("Error", "Check due date format and max score.", parent=d)
            if not e_title.get().strip():
                return messagebox.showerror("Error", "Title is required.", parent=d)
            aid = run("INSERT INTO assignments(title,description,type,instructor_id,due_date,max_score) "
                      "VALUES(%s,%s,%s,%s,%s,%s)",
                      (e_title.get().strip(), t_desc.get("1.0", "end").strip(), c_type.get(),
                       self.user["id"], due, mx), write=True)
            run("INSERT INTO submissions(assignment_id,student_id) SELECT %s, id FROM students",
                (aid,), write=True)
            d.destroy()
            self.load_assignments()

        ttk.Button(d, text="Add", command=ok).grid(row=5, column=1, sticky="e", padx=6, pady=8)

    @safe
    def delete_assignment(self):
        aid = self.sel_assignment()
        if aid and messagebox.askyesno("Confirm", "Delete this assignment and all its submissions?"):
            run("DELETE FROM assignments WHERE id=%s", (aid,), write=True)
            self.load_assignments()

class StudentWin(tk.Toplevel):
    def __init__(self, login, user):
        super().__init__(login)
        self.login, self.user, self.rows = login, user, {}
        self.title(f"Student - {user['name']}")
        self.geometry("920x640")
        self.protocol("WM_DELETE_WINDOW", login.destroy)

        ttk.Label(self, text=f"{user['name']}   |   {user['year_level']}   |   {user['email']}",
                  font=("", 13, "bold")).pack(pady=6)

        f1 = ttk.LabelFrame(self, text="My assignments / exams")
        f1.pack(fill="both", expand=True, padx=8, pady=4)
        box = ttk.Frame(f1); box.pack(fill="both", expand=True)
        self.t = tree(box, [("title", "Title"), ("type", "Type"), ("inst", "Instructor"),
                            ("due", "Due date"), ("status", "Status"), ("score", "Score")],
                      [230, 80, 150, 140, 110, 90], 9)
        self.t.bind("<<TreeviewSelect>>", lambda e: self.show())
        self.lbl_avg = ttk.Label(f1, text="")
        self.lbl_avg.pack(anchor="w", padx=4, pady=2)

        f2 = ttk.LabelFrame(self, text="Details & notes")
        f2.pack(fill="x", padx=8, pady=4)
        ttk.Label(f2, text="Task description:").grid(row=0, column=0, sticky="nw")
        self.t_desc = tk.Text(f2, height=3, width=45, state="disabled", bg="#f0f0f0")
        self.t_desc.grid(row=0, column=1, padx=4, pady=2)
        ttk.Label(f2, text="Instructor note:").grid(row=0, column=2, sticky="nw")
        self.t_inst = tk.Text(f2, height=3, width=45, state="disabled", bg="#f0f0f0")
        self.t_inst.grid(row=0, column=3, padx=4, pady=2)
        ttk.Label(f2, text="My note:").grid(row=1, column=0, sticky="nw")
        self.t_mine = tk.Text(f2, height=3, width=45)
        self.t_mine.grid(row=1, column=1, padx=4, pady=2)
        bt = ttk.Frame(f2); bt.grid(row=1, column=3, sticky="e")
        ttk.Button(bt, text="Save note", command=self.save_note).pack(side="left", padx=4)
        ttk.Button(bt, text="Submit work", command=self.submit).pack(side="left", padx=4)
        ttk.Button(bt, text="Logout", command=self.logout).pack(side="left", padx=4)

        self.load()

    def logout(self):
        self.destroy()
        self.login.deiconify()

    @safe
    def load(self):
        self.t.delete(*self.t.get_children())
        rows = run("""SELECT s.id, a.title, a.type, a.description, a.due_date, a.max_score,
                             i.name AS inst, s.status, s.score, s.student_note, s.instructor_note
                      FROM submissions s JOIN assignments a ON a.id=s.assignment_id
                      JOIN instructors i ON i.id=a.instructor_id
                      WHERE s.student_id=%s ORDER BY a.due_date""", (self.user["id"],))
        self.rows = {r["id"]: r for r in rows}
        got = mx = 0
        for r in rows:
            sc = "" if r["score"] is None else f"{r['score']} / {r['max_score']}"
            if r["score"] is not None:
                got += float(r["score"]); mx += r["max_score"]
            self.t.insert("", "end", iid=str(r["id"]),
                          values=(r["title"], r["type"], r["inst"], dt(r["due_date"]), r["status"], sc))
        self.lbl_avg.config(text=f"Overall: {got:.1f} / {mx}  ({got / mx * 100:.1f}%)" if mx
                            else "No graded work yet.")

    def current(self):
        s = self.t.selection()
        return self.rows[int(s[0])] if s else None

    def show(self):
        r = self.current()
        if r:
            set_text(self.t_desc, r["description"], True)
            set_text(self.t_inst, r["instructor_note"], True)
            set_text(self.t_mine, r["student_note"])

    @safe
    def save_note(self):
        r = self.current()
        if not r:
            return messagebox.showinfo("Select", "Select an assignment first.")
        run("UPDATE submissions SET student_note=%s WHERE id=%s",
            (self.t_mine.get("1.0", "end").strip(), r["id"]), write=True)
        self.reload_keep(r["id"])
        messagebox.showinfo("Saved", "Note saved.")

    @safe
    def submit(self):
        r = self.current()
        if not r:
            return messagebox.showinfo("Select", "Select an assignment first.")
        now = datetime.now()
        status = "Late" if now > r["due_date"] else "Submitted"
        run("UPDATE submissions SET status=%s, submitted_at=%s, student_note=%s WHERE id=%s",
            (status, now, self.t_mine.get("1.0", "end").strip(), r["id"]), write=True)
        self.reload_keep(r["id"])
        messagebox.showinfo("Submitted", f"Marked as: {status}")

    def reload_keep(self, sid):
        self.load()
        self.t.selection_set(str(sid))

class Login(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Performance Tracker")
        self.geometry("360x200")
        self.users = []
        ttk.Label(self, text="Performance Tracking System", font=("", 14, "bold")).pack(pady=10)
        f = ttk.Frame(self); f.pack()
        ttk.Label(f, text="Role").grid(row=0, column=0, pady=5, sticky="e")
        self.role = ttk.Combobox(f, values=["Student", "Instructor"], state="readonly", width=28)
        self.role.set("Student")
        self.role.grid(row=0, column=1, padx=6)
        self.role.bind("<<ComboboxSelected>>", lambda e: self.load_users())
        ttk.Label(f, text="Name").grid(row=1, column=0, pady=5, sticky="e")
        self.user = ttk.Combobox(f, state="readonly", width=28)
        self.user.grid(row=1, column=1, padx=6)
        ttk.Button(self, text="Open", command=self.open).pack(pady=14)
        self.load_users()

    @safe
    def load_users(self):
        table = "students" if self.role.get() == "Student" else "instructors"
        self.users = run(f"SELECT * FROM {table} ORDER BY name")
        self.user["values"] = [u["name"] for u in self.users]
        if self.users:
            self.user.current(0)

    def open(self):
        i = self.user.current()
        if i < 0:
            return
        self.withdraw()
        win = StudentWin if self.role.get() == "Student" else InstructorWin
        win(self, self.users[i])


if __name__ == "__main__":
    Login().mainloop()
