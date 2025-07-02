import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from mysql.connector import Error

class PrettyStudentManagement:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Student Management System")
        self.root.geometry("1200x750")
        self.root.configure(bg="#f0f2f5")
        
        # Set theme colors
        self.primary_color = "#4e73df"
        self.secondary_color = "#1cc88a"
        self.danger_color = "#e74a3b"
        self.light_bg = "#f8f9fc"
        self.dark_text = "#5a5c69"
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom style configurations
        self.style.configure('TFrame', background=self.light_bg)
        self.style.configure('TLabel', background=self.light_bg, foreground=self.dark_text)
        self.style.configure('TButton', font=('Segoe UI', 10), padding=6)
        self.style.configure('Header.TLabel', font=('Segoe UI', 16, 'bold'), foreground=self.primary_color)
        self.style.configure('Primary.TButton', background=self.primary_color, foreground='white')
        self.style.configure('Success.TButton', background=self.secondary_color, foreground='white')
        self.style.configure('Danger.TButton', background=self.danger_color, foreground='white')
        
        # Database connection
        self.connection = self.create_connection()
        if not self.connection:
            messagebox.showerror("Error", "Failed to connect to database")
            self.root.destroy()
            return
        
        self.create_widgets()
        self.load_students()

    def create_connection(self):
        try:
            return mysql.connector.connect(
                host='localhost',
                user='root',
                password='Founas@123',
                database='student_man'
            )
        except Error as e:
            messagebox.showerror("Database Error", f"Connection failed: {e}")
            return None

    def create_widgets(self):
        # Header Frame
        header_frame = ttk.Frame(self.root, style='TFrame')
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(header_frame, text="🎓 Student Management System", 
                 style='Header.TLabel').pack(side=tk.LEFT)
        
        # Main Container
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))
        
        # Sidebar Frame
        sidebar_frame = ttk.Frame(main_frame, width=200, style='TFrame')
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0,10))
        
        # Sidebar Buttons
        buttons = [
            ("➕ Add Student", self.add_student_dialog, 'Primary.TButton'),
            ("✏️ Edit Marks", self.edit_marks_dialog, 'Primary.TButton'),
            ("🔄 Refresh", self.load_students, 'Success.TButton'),
            ("❌ Exit", self.root.quit, 'Danger.TButton')
        ]
        
        for text, command, style in buttons:
            btn = ttk.Button(sidebar_frame, text=text, command=command, style=style)
            btn.pack(fill=tk.X, pady=5)
        
        # Main Content Frame
        content_frame = ttk.Frame(main_frame, style='TFrame')
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Treeview with Scrollbars
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, columns=(
            "ID", "Name", "Maths", "Physics", "Chemistry", "Biology", "English", 
            "Total", "CGPA", "Status"), show="headings", style='Treeview')
        
        # Configure Treeview style
        self.style.configure('Treeview', font=('Segoe UI', 10), rowheight=25)
        self.style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
        self.style.map('Treeview', background=[('selected', self.primary_color)])
        
        # Configure columns
        columns = [
            ("ID", 50), ("Name", 150), ("Maths", 70), ("Physics", 70), 
            ("Chemistry", 80), ("Biology", 70), ("English", 70),
            ("Total", 70), ("CGPA", 70), ("Status", 120)
        ]
        
        for col, width in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor=tk.CENTER)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        x_scroll = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        
        # Grid layout for tree and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Status Bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                             relief=tk.SUNKEN, anchor=tk.W, style='TLabel')
        status_bar.pack(fill=tk.X, padx=10, pady=(0,10))

    def calculate_cgpa(self, marks_list):
        total = sum(marks_list)
        percentage = (total / (len(marks_list) * 100)) * 100
        cgpa = min(10.0, percentage / 9.5)
        return round(cgpa, 2)

    def check_pass_status(self, marks):
        failed_subjects = []
        subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
        
        for i, mark in enumerate(marks):
            if mark < 45:
                failed_subjects.append(subjects[i])
        
        if failed_subjects:
            return ('Failed', failed_subjects)
        return ('Passed', [])

    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT student_id, student_name, 
                       marks1, marks2, marks3, marks4, marks5,
                       total_marks, cgpa, pass_fail_status
                FROM students
                ORDER BY student_id
            """)
            
            students = cursor.fetchall()
            
            for student in students:
                marks = [float(student[f'marks{i}']) for i in range(1, 6)]
                status, failed_subjects = self.check_pass_status(marks)
                status_display = "✅ Passed" if status == 'Passed' else f"❌ Failed in: {', '.join(failed_subjects)}"
                
                # Tag for alternating row colors
                tags = ('evenrow',) if student['student_id'] % 2 == 0 else ('oddrow',)
                
                self.tree.insert("", tk.END, values=(
                    student['student_id'],
                    student['student_name'],
                    student['marks1'],
                    student['marks2'],
                    student['marks3'],
                    student['marks4'],
                    student['marks5'],
                    student['total_marks'],
                    student['cgpa'],
                    status_display
                ), tags=tags)
            
            # Configure row tags
            self.tree.tag_configure('evenrow', background='#f8f9fc')
            self.tree.tag_configure('oddrow', background='#ffffff')
            
            self.status_var.set(f"✔ Loaded {len(students)} student records")
                
        except Error as e:
            messagebox.showerror("Database Error", f"Error retrieving students: {e}")
            self.status_var.set("✖ Error loading records")
        finally:
            if cursor:
                cursor.close()

    def add_student_dialog(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("➕ Add New Student")
        add_window.geometry("400x450")
        add_window.resizable(False, False)
        add_window.grab_set()  # Make window modal
        
        # Form fields
        ttk.Label(add_window, text="Student Name:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        name_entry = ttk.Entry(add_window, width=30)
        name_entry.grid(row=0, column=1, padx=10, pady=10)
        
        subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
        entries = []
        
        for i, subject in enumerate(subjects, start=1):
            ttk.Label(add_window, text=f"{subject} Marks (0-100):").grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
            entry = ttk.Entry(add_window, width=10)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
            entries.append(entry)
        
        def save_student():
            try:
                # Validate name
                name = name_entry.get().strip()
                if not name:
                    messagebox.showerror("Error", "Student name cannot be empty")
                    return
                
                # Validate marks
                marks = []
                for i, entry in enumerate(entries):
                    try:
                        mark = float(entry.get())
                        if mark < 0 or mark > 100:
                            messagebox.showerror("Error", f"{subjects[i]} marks must be between 0-100")
                            return
                        marks.append(mark)
                    except ValueError:
                        messagebox.showerror("Error", f"Invalid marks for {subjects[i]}")
                        return
                
                # Calculate total and CGPA
                total = sum(marks)
                cgpa = self.calculate_cgpa(marks)
                status, _ = self.check_pass_status(marks)
                
                # Insert into database
                cursor = self.connection.cursor()
                query = """INSERT INTO students 
                          (student_name, subject1, marks1, subject2, marks2, 
                           subject3, marks3, subject4, marks4, subject5, marks5, 
                           total_marks, cgpa, pass_fail_status)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                cursor.execute(query, (
                    name,
                    'Maths', marks[0],
                    'Physics', marks[1],
                    'Chemistry', marks[2],
                    'Biology', marks[3],
                    'English', marks[4],
                    total, cgpa, status
                ))
                self.connection.commit()
                
                messagebox.showinfo("Success", "Student added successfully!")
                self.load_students()
                add_window.destroy()
                
            except Error as e:
                messagebox.showerror("Database Error", f"Error adding student: {e}")
                self.connection.rollback()
            finally:
                if cursor:
                    cursor.close()
        
        # Button frame
        button_frame = ttk.Frame(add_window)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Save", command=save_student, style='Success.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=add_window.destroy, style='Danger.TButton').pack(side=tk.LEFT, padx=10)

    def edit_marks_dialog(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a student to edit")
            return
        
        student_id = self.tree.item(selected[0], 'values')[0]
        student_name = self.tree.item(selected[0], 'values')[1]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title(f"✏️ Edit Marks for {student_name}")
        edit_window.geometry("400x450")
        edit_window.resizable(False, False)
        edit_window.grab_set()  # Make window modal
        
        # Get current marks
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT marks1, marks2, marks3, marks4, marks5
                FROM students
                WHERE student_id = %s
            """, (student_id,))
            
            student = cursor.fetchone()
            if not student:
                messagebox.showerror("Error", "Student not found")
                edit_window.destroy()
                return
            
            # Display student info
            ttk.Label(edit_window, text=f"Student: {student_name}", font=('Segoe UI', 10, 'bold')).pack(pady=10)
            
            subjects = ['Maths', 'Physics', 'Chemistry', 'Biology', 'English']
            entries = []
            
            for i, subject in enumerate(subjects, start=1):
                frame = ttk.Frame(edit_window)
                frame.pack(fill=tk.X, padx=10, pady=5)
                
                ttk.Label(frame, text=f"{subject} Marks:", width=15).pack(side=tk.LEFT)
                entry = ttk.Entry(frame, width=10)
                entry.insert(0, student[f'marks{i}'])
                entry.pack(side=tk.LEFT)
                entries.append(entry)
            
            def save_changes():
                try:
                    # Validate marks
                    marks = []
                    for i, entry in enumerate(entries):
                        try:
                            mark = float(entry.get())
                            if mark < 0 or mark > 100:
                                messagebox.showerror("Error", f"{subjects[i]} marks must be between 0-100")
                                return
                            marks.append(mark)
                        except ValueError:
                            messagebox.showerror("Error", f"Invalid marks for {subjects[i]}")
                            return
                    
                    # Calculate total and CGPA
                    total = sum(marks)
                    cgpa = self.calculate_cgpa(marks)
                    status, _ = self.check_pass_status(marks)
                    
                    # Update database
                    cursor = self.connection.cursor()
                    cursor.execute("""
                        UPDATE students 
                        SET marks1 = %s, marks2 = %s, marks3 = %s, marks4 = %s, marks5 = %s,
                            total_marks = %s, cgpa = %s, pass_fail_status = %s
                        WHERE student_id = %s
                    """, (
                        marks[0], marks[1], marks[2], marks[3], marks[4],
                        total, cgpa, status, student_id
                    ))
                    self.connection.commit()
                    
                    messagebox.showinfo("Success", "Marks updated successfully!")
                    self.load_students()
                    edit_window.destroy()
                    
                except Error as e:
                    messagebox.showerror("Database Error", f"Error updating marks: {e}")
                    self.connection.rollback()
                finally:
                    if cursor:
                        cursor.close()
            
            # Button frame
            button_frame = ttk.Frame(edit_window)
            button_frame.pack(pady=20)
            
            ttk.Button(button_frame, text="Save Changes", command=save_changes, style='Success.TButton').pack(side=tk.LEFT, padx=10)
            ttk.Button(button_frame, text="Cancel", command=edit_window.destroy, style='Danger.TButton').pack(side=tk.LEFT, padx=10)
            
        except Error as e:
            messagebox.showerror("Database Error", f"Error retrieving student data: {e}")
            edit_window.destroy()
        finally:
            if cursor:
                cursor.close()

    def __del__(self):
        if hasattr(self, 'connection') and self.connection.is_connected():
            self.connection.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = PrettyStudentManagement(root)
    root.mainloop()