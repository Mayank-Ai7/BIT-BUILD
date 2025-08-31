import os
import threading
import qrcode
import cv2
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image as PILImage
from datetime import datetime, timedelta

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import mainthread
from kivy.core.window import Window

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from utils.helpers import get_db_connection
from kivy.utils import get_color_from_hex

from utils.helpers import (
    # ensure_attendance_csv,
    get_wifi_ssid,
    update_attendance,
    TEACHER_CREDENTIALS,
    EXPECTED_WIFI,
    # CSV_FILE,
    # SUBJECTS,
    students,
)

# Screens
from screens.login import LoginScreen
from screens.student_login import StudentLoginScreen
from screens.teacher_login import TeacherLoginScreen
from screens.student_dashboard import StudentDashboardScreen
from screens.teacher_dashboard import TeacherDashboardScreen
from screens.attendance_view import AttendanceViewScreen
from screens.student_attendance import StudentAttendanceScreen

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView

class AttendanceApp(App):
    def build(self):
        # ensure_attendance_csv()
        Window.size = (450, 700)

        self.sm = ScreenManager()

        # create screens and add to manager
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(StudentLoginScreen(name="student_login"))
        self.sm.add_widget(TeacherLoginScreen(name="teacher_login"))
        self.sm.add_widget(StudentDashboardScreen(name="student_dashboard"))
        self.sm.add_widget(TeacherDashboardScreen(name="teacher_dashboard"))

        self.attendance_view_screen = AttendanceViewScreen(name="attendance_view")
        self.sm.add_widget(self.attendance_view_screen)

        self.student_attendance_screen = StudentAttendanceScreen(name="student_attendance")
        self.sm.add_widget(self.student_attendance_screen)

        # runtime state
        self.student_name = None
        self.current_class_id = None
        self.current_student_id = None

        return self.sm

    # ---------------- navigation helpers ----------------
    def go_to_screen(self, screen_name):
        self.sm.current = screen_name

    def logout_to_login(self):
        self.student_name = None
        self.current_class_id = None
        self.go_to_screen("login")

    # ---------------- generic popup helper (replaces messagebox) ----------------
    def popup(self, title, msg):
        p = Popup(title=title, content=Label(text=msg), size_hint=(0.8, 0.4))
        p.open()

    # ---------------- login validation (matches original logic) ----------------
    def validate_login(self, user_type, user_id, password):
        if user_type == "Student":
            if user_id in students and students[user_id][1] == password:
                self.student_name = students[user_id][0]
                self.current_student_id = students[user_id][2]
                self.popup("Login Success", f"Welcome, {self.student_name}")
                self.go_to_screen("student_dashboard")
            else:
                self.popup("Wrong Credentials", "Invalid ID or Password")

        elif user_type == "Teacher":
            for class_id, (stored_id, stored_pass, teacher_id) in TEACHER_CREDENTIALS.items():
                if user_id == stored_id and password == stored_pass:
                    self.current_class_id = class_id
                    self.popup("Login Success", f"Welcome, {user_id}!")
                    # update teacher dashboard label & image
                    t_screen = self.sm.get_screen("teacher_dashboard")
                    t_screen.class_id_label.text = f"Teacher Dashboard ({class_id})"
                    # if qr already exists, show it
                    img_path = f"qr_codes/{class_id}.png"
                    if os.path.exists(img_path):
                        t_screen.qr_image.source = img_path
                        t_screen.qr_image.reload()
                    self.go_to_screen("teacher_dashboard")
                    return
            self.popup("Invalid Credentials", "Incorrect User ID or Password!")


    def show_subject_selection(self):
        """Show popup for subject selection"""
        if not self.current_class_id:
            self.popup("Error", "No teacher logged in")
            return

        try:
            # Get subjects for current teacher
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT subject_id, subject_name 
                        FROM Subjects 
                        WHERE teacher_id = (
                            SELECT teacher_id FROM Teachers 
                            WHERE name = %s
                        )
                    """, (self.current_class_id,))
                    subjects = cur.fetchall()

            if not subjects:
                self.popup("Error", "No subjects found for this teacher")
                return

            # Create popup content
            content = BoxLayout(orientation='vertical', spacing=10, padding=10)
            modal = ModalView(size_hint=(0.8, 0.8))

            for subject_id, subject_name in subjects:
                btn = Button(
                    text=subject_name,
                    size_hint_y=None,
                    height=50,
                    background_color=get_color_from_hex("#488155ff")
                )
                btn.bind(on_press=lambda x, sid=subject_id, sname=subject_name: 
                        self.generate_qr_for_subject(sid, sname, modal))
                content.add_widget(btn)

            # Add cancel button
            cancel_btn = Button(
                text="Cancel",
                size_hint_y=None,
                height=50,
                background_color=get_color_from_hex("#adb5bdff")
            )
            cancel_btn.bind(on_press=modal.dismiss)
            content.add_widget(cancel_btn)

            modal.add_widget(content)
            modal.open()

        except Exception as e:
            self.popup("Error", f"Failed to load subjects: {e}")

    # ---------------- QR generation (ties to teacher dashboard) ----------------
    def generate_qr_for_subject(self, subject_id, subject_name, modal):
    # """Generate QR code for selected subject and update database"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    # Update ongoing_classes
                    cur.execute("""
                                UPDATE Ongoing_classes
                                SET 
                                    subject_id = %s,  
                                    total_class_completed = total_class_completed + 1,
                                    marked_at = CURRENT_TIMESTAMP
                                WHERE ongoing_class_id = 1; 
                    """, (subject_id,))
                    cur.execute("""
                                UPDATE Subjects
                                SET
                                    total_classes_held = total_classes_held + 1
                                WHERE subject_id = %s;
                    """, (subject_id,))

                    # Generate QR code
                    qr = qrcode.QRCode(version=1, box_size=10, border=5)
                    qr.add_data(str(subject_id))  # Use subject_id in QR
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")

                    if not os.path.exists("qr_codes"):
                        os.makedirs("qr_codes")

                    img_path = f"qr_codes/{subject_name}.png"
                    img.save(img_path)

                    # Resize image
                    try:
                        pil_img = PILImage.open(img_path)
                        pil_img.thumbnail((200, 200))
                        pil_img.save(img_path)
                    except Exception as e:
                        print(f"Error resizing image: {e}")

                    # Update teacher dashboard
                    t_screen = self.sm.get_screen("teacher_dashboard")
                    t_screen.qr_image.source = img_path
                    t_screen.qr_image.reload()

                    conn.commit()
                    modal.dismiss()
                    self.popup("Success", f"QR generated for {subject_name}")

        except Exception as e:
            self.popup("Error", f"Failed to generate QR: {e}")


    # ---------------- QR scanning (threaded) ----------------
    def start_scan_thread(self):
        t = threading.Thread(target=self._scan_qr_thread, daemon=True)
        t.start()

    def _scan_qr_thread(self):
        """Handles QR code scanning and attendance marking in a separate thread, displaying camera window"""
        try:
            # Check WiFi SSID first
            current_ssid = get_wifi_ssid()
            if current_ssid != EXPECTED_WIFI:
                self.show_scan_result("Error: Please connect to the correct WiFi network")
                return

            cap = cv2.VideoCapture(0)
            while True:
                ret, frame = cap.read()
                if not ret:
                    self.show_scan_result("Error: Unable to access camera")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                decoded_objects = decode(gray)

                # Display camera window
                cv2.imshow("Scan QR Code - Press Q to Quit", frame)

                for obj in decoded_objects:
                    try:
                        subject_id = int(obj.data.decode('utf-8'))

                        # Connect to database
                        with get_db_connection() as conn:
                            with conn.cursor() as cur:
                                # Check if subject exists in ongoing classes and within time limit
                                cur.execute("""
                                    SELECT subject_id 
                                    FROM Ongoing_classes 
                                    WHERE subject_id = %s 
                                    AND NOW() BETWEEN marked_at AND marked_at + INTERVAL '1 hour'
                                """, (subject_id,))
                                ongoing_class = cur.fetchone()

                                if not ongoing_class:
                                    self.show_scan_result("Error: Class not active or time expired")
                                    cap.release()
                                    cv2.destroyAllWindows()
                                    return

                                # Check if student already marked attendance in this hour
                                cur.execute("""
                                    SELECT attendance_id 
                                    FROM Attendance 
                                    WHERE subject_id = %s 
                                    AND student_id = %s 
                                    AND marked_at > NOW() - INTERVAL '1 hour'
                                """, (subject_id, self.current_student_id))
                                if cur.fetchone():
                                    self.show_scan_result("Error: Attendance already marked for this hour")
                                    cap.release()
                                    cv2.destroyAllWindows()
                                    return

                                # Mark attendance
                                cur.execute("""
                                    INSERT INTO Attendance (subject_id, student_id, marked_at)
                                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                                """, (subject_id, self.current_student_id))
                                conn.commit()
                                self.show_scan_result("Attendance marked successfully!")
                                cap.release()
                                cv2.destroyAllWindows()
                                return
                    except ValueError:
                        self.show_scan_result("Error: Invalid QR code")
                        cap.release()
                        cv2.destroyAllWindows()
                        return
                    except Exception as e:
                        self.show_scan_result(f"Error: {str(e)}")
                        cap.release()
                        cv2.destroyAllWindows()
                        return

                # Exit on 'q' key
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            cap.release()
            cv2.destroyAllWindows()
        except Exception as e:
            self.show_scan_result(f"Error: {str(e)}")
        finally:
            if 'cap' in locals():
                cap.release()
            cv2.destroyAllWindows()

    # Add this method to the AttendanceApp class
    @mainthread
    def show_scan_result(self, message):
        """
        Shows scan result in a popup. Uses @mainthread decorator since 
        it's called from the scanning thread to update UI
        """
        popup = Popup(
            title='Scan Result',
            content=Label(text=message),
            size_hint=(None, None),
            size=(400, 200),
            background_color=get_color_from_hex("#f8f9faff")
        )
        popup.open()

    # ---------------- screens to show attendance ----------------
    def show_student_attendance_screen(self):
        """Display attendance screen for currently logged in student"""
        if not self.student_name:
            self.popup("Error", "No student logged in")
            return

        try:
            # populate_for_student now uses database queries instead of CSV
            self.student_attendance_screen.populate_for_student(self.student_name)
            self.go_to_screen("student_attendance")
        except Exception as e:
            self.popup("Error", f"Failed to load attendance data: {e}")


    # Add after show_student_attendance_screen method
    def show_teacher_attendance_screen(self):
        """Display attendance overview screen for teacher view"""
        if not self.current_class_id:
            self.popup("Error", "No teacher logged in")
            return

        try:
            from utils.helpers import get_all_attendance
            attendance_data = get_all_attendance()
            self.attendance_view_screen.populate_from_database(attendance_data)
            self.go_to_screen("attendance_view")
        except Exception as e:
            self.popup("Error", f"Failed to load attendance data: {e}")