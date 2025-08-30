import os
import threading
import qrcode
import cv2
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import mainthread
from kivy.core.window import Window

from utils.helpers import (
    ensure_attendance_csv,
    get_wifi_ssid,
    update_attendance,
    TEACHER_CREDENTIALS,
    EXPECTED_WIFI,
    CSV_FILE,
    SUBJECTS,
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


class AttendanceApp(App):
    def build(self):
        ensure_attendance_csv()
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
                self.popup("Login Success", f"Welcome, {self.student_name}")
                self.go_to_screen("student_dashboard")
            else:
                self.popup("Wrong Credentials", "Invalid ID or Password")

        elif user_type == "Teacher":
            for class_id, (stored_id, stored_pass) in TEACHER_CREDENTIALS.items():
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

    # ---------------- QR generation (ties to teacher dashboard) ----------------
    def generate_qr_current_class(self):
        if not self.current_class_id:
            self.popup("Error", "No class selected.")
            return

        class_id = self.current_class_id
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(class_id)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        if not os.path.exists("qr_codes"):
            os.makedirs("qr_codes")

        img_path = f"qr_codes/{class_id}.png"
        img.save(img_path)

        # Resize via PIL (keep parity with original behavior)
        try:
            pil_img = PILImage.open(img_path)
            pil_img.thumbnail((200, 200))
            pil_img.save(img_path)
        except Exception:
            pass

        t_screen = self.sm.get_screen("teacher_dashboard")
        t_screen.qr_image.source = img_path
        t_screen.qr_image.reload()
        self.popup("Success", f"QR generated for {class_id}")

    # ---------------- QR scanning (threaded) ----------------
    def start_scan_thread(self):
        t = threading.Thread(target=self._scan_qr_thread, daemon=True)
        t.start()

    def _scan_qr_thread(self):
        cap = cv2.VideoCapture(0)
        print("Scanning... Place the QR code in front of the camera.")

        class_id = None
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            decoded_objs = decode(frame)
            for obj in decoded_objs:
                class_id = obj.data.decode('utf-8')
                break
            cv2.imshow("QR Code Scanner", frame)
            if class_id:
                break
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

        if class_id:
            self.process_scan_result(class_id)
        else:
            self.popup("Error", "No QR code detected or scan cancelled.")

    @mainthread
    def process_scan_result(self, class_id):
        if class_id and class_id in SUBJECTS:
            wifi_ssid = get_wifi_ssid()
            if wifi_ssid == EXPECTED_WIFI:
                if update_attendance(self.student_name, class_id):
                    self.popup("Success", f"Attendance marked for {class_id}")
                else:
                    self.popup("Error", "Invalid Class ID")
            else:
                self.popup("Error", "Wrong WiFi Network")
        else:
            self.popup("Error", "Invalid QR Code")

    # ---------------- screens to show attendance ----------------
    def show_teacher_attendance_screen(self):
        try:
            df = pd.read_csv(CSV_FILE)
            self.attendance_view_screen.populate_from_csv(df)
            self.go_to_screen("attendance_view")
        except Exception as e:
            self.popup("Error", f"Failed to load attendance: {e}")

    def show_student_attendance_screen(self):
        if not self.student_name:
            self.popup("Error", "No student logged in")
            return
        self.student_attendance_screen.populate_for_student(self.student_name)
        self.go_to_screen("student_attendance")
