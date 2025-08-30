# attendance_kivy.py
# All non-GUI logic (QR gen, scan, CSV update, WiFi check, credentials) is preserved.

import os
import threading
import subprocess
import qrcode
import cv2
import pandas as pd
from pyzbar.pyzbar import decode
from PIL import Image as PILImage

# Kivy imports (replaces all tkinter imports and ttk)
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.utils import get_color_from_hex

# ---------- Data / constants (unchanged from your original code) ----------
TEACHER_CREDENTIALS = {
    "DMS": ("DMS_teacher", "passDMS"),
    "COA": ("COA_teacher", "passCOA"),
    "TOC": ("TOC_teacher", "passTOC"),
    "DBMS": ("DBMS_teacher", "passDBMS"),
    "OOPSJ": ("OOPSJ_teacher", "passOOPSJ"),
    "LMP-2": ("LMP2_teacher", "passLMP2"),
    "LOOPSJ": ("LOOPSJ_teacher", "passLOOPSJ"),
    "LCOA": ("LCOA_teacher", "passLCOA"),
    "LDBMS": ("LDBMS_teacher", "passLDBMS")
}
EXPECTED_WIFI = "Mayank"
CSV_FILE = "attendance.csv"

students = {
    "11": ("Arin", "arin"),
    "28": ("Mayank", "mayank"),
    "19": ("Gatik", "gatik"),
}

SUBJECTS = ["DMS", "COA", "TOC", "DBMS", "OOPSJ", "LMP-2", "LOOPSJ", "LCOA", "LDBMS"]


# ---------- Helper functions preserved with minimal changes ----------
def get_wifi_ssid():
    """
    Preserved logic: call netsh and parse output.
    """
    try:
        result = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("utf-8", errors="ignore")
        for line in result.split("\n"):
            if "SSID" in line and ":" in line:
                # same parsing approach as original
                return line.split(":", 1)[1].strip()
    except Exception as e:
        print("Error getting WiFi SSID:", e)
    return None


def update_attendance(student_name, subject):
    """
    Same logic as original: load CSV, increment the subject column for the named student.
    """
    try:
        df = pd.read_csv(CSV_FILE)
        if subject in df.columns and student_name in df["Name"].values:
            # safer increment to avoid SettingWithCopy warnings
            df.loc[df["Name"] == student_name, subject] = df.loc[df["Name"] == student_name, subject].astype(int) + 1
            df.to_csv(CSV_FILE, index=False)
            print(f"Attendance updated for {student_name} in {subject}.")
            return True
        print("Invalid Subject or Student Name")
        return False
    except Exception as e:
        print("Error updating attendance:", e)
        return False


def ensure_attendance_csv():
    if not os.path.exists(CSV_FILE):
        # Create a DataFrame with Name and all subjects, values set to 0
        data = []
        for sid, (name, _) in students.items():
            row = {"Name": name}
            for subj in SUBJECTS:
                row[subj] = 0
            data.append(row)
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
        print("Created new attendance.csv")


# ---------- Screens (Kivy) ----------

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=get_color_from_hex("#8F9198FF"))
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # Absolute positioning for a centered column
        self.heading = Label(
            text="[b]Attendance System[/b]",
            markup=True,
            font_size=32,
            color=get_color_from_hex("#FFFFFFFF"),
            size_hint=(None, None),
            size=(400, 60),
            pos_hint={"center_x": 0.5, "top": 0.92}
        )
        self.add_widget(self.heading)

        self.btn_student = Button(
            text="Student Login",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.75},
            background_color=get_color_from_hex("#62AFE2FF"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.btn_student.bind(on_press=lambda inst: App.get_running_app().go_to_screen("student_login"))
        self.add_widget(self.btn_student)

        self.btn_teacher = Button(
            text="Teacher Login",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.62},
            background_color=get_color_from_hex("#488155ff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.btn_teacher.bind(on_press=lambda inst: App.get_running_app().go_to_screen("teacher_login"))
        self.add_widget(self.btn_teacher)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos


class StudentLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=get_color_from_hex("#f0f4f8ff"))
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.heading = Label(
            text="[b]Student Login[/b]",
            markup=True,
            font_size=26,
            color=get_color_from_hex("#22223bff"),
            size_hint=(None, None),
            size=(400, 50),
            pos_hint={"center_x": 0.5, "top": 0.92}
        )
        self.add_widget(self.heading)

        self.label_user = Label(
            text="User ID:",
            size_hint=(None, None),
            size=(120, 30),
            color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.80}
        )
        self.add_widget(self.label_user)

        self.user_id_input = TextInput(
            multiline=False,
            size_hint=(None, None),
            size=(280, 40),
            background_color=get_color_from_hex("#e0e1ddff"),
            foreground_color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.75}
        )
        self.add_widget(self.user_id_input)

        self.label_pass = Label(
            text="Password:",
            size_hint=(None, None),
            size=(120, 30),
            color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.70}
        )
        self.add_widget(self.label_pass)

        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint=(None, None),
            size=(280, 40),
            background_color=get_color_from_hex("#e0e1ddff"),
            foreground_color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.65}
        )
        self.add_widget(self.password_input)

        self.login_btn = Button(
            text="Login",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={"center_x": 0.5, "top": 0.55},
            background_color=get_color_from_hex("#4ea8deff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.login_btn.bind(on_press=self.attempt_login)
        self.add_widget(self.login_btn)

        self.back_btn = Button(
            text="Back",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={"center_x": 0.5, "top": 0.45},
            background_color=get_color_from_hex("#adb5bdff"),
            color=get_color_from_hex("#22223bff"),
            bold=True,
            background_normal=""
        )
        self.back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("login"))
        self.add_widget(self.back_btn)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def attempt_login(self, instance):
        user_id = self.user_id_input.text.strip()
        password = self.password_input.text.strip()
        App.get_running_app().validate_login("Student", user_id, password)


class TeacherLoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=get_color_from_hex("#f0f4f8ff"))
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.heading = Label(
            text="[b]Teacher Login[/b]",
            markup=True,
            font_size=26,
            color=get_color_from_hex("#22223bff"),
            size_hint=(None, None),
            size=(400, 50),
            pos_hint={"center_x": 0.5, "top": 0.92}
        )
        self.add_widget(self.heading)

        self.label_user = Label(
            text="User ID:",
            size_hint=(None, None),
            size=(120, 30),
            color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.80}
        )
        self.add_widget(self.label_user)

        self.user_id_input = TextInput(
            multiline=False,
            size_hint=(None, None),
            size=(280, 40),
            background_color=get_color_from_hex("#e0e1ddff"),
            foreground_color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.75}
        )
        self.add_widget(self.user_id_input)

        self.label_pass = Label(
            text="Password:",
            size_hint=(None, None),
            size=(120, 30),
            color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.70}
        )
        self.add_widget(self.label_pass)

        self.password_input = TextInput(
            password=True,
            multiline=False,
            size_hint=(None, None),
            size=(280, 40),
            background_color=get_color_from_hex("#e0e1ddff"),
            foreground_color=get_color_from_hex("#22223bff"),
            pos_hint={"center_x": 0.5, "top": 0.65}
        )
        self.add_widget(self.password_input)

        self.login_btn = Button(
            text="Login",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={"center_x": 0.5, "top": 0.55},
            background_color=get_color_from_hex("#488155ff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.login_btn.bind(on_press=self.attempt_login)
        self.add_widget(self.login_btn)

        self.back_btn = Button(
            text="Back",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={"center_x": 0.5, "top": 0.45},
            background_color=get_color_from_hex("#adb5bdff"),
            color=get_color_from_hex("#22223bff"),
            bold=True,
            background_normal=""
        )
        self.back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("login"))
        self.add_widget(self.back_btn)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def attempt_login(self, instance):
        user_id = self.user_id_input.text.strip()
        password = self.password_input.text.strip()
        App.get_running_app().validate_login("Teacher", user_id, password)


class StudentDashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=get_color_from_hex("#f0f4f8ff"))
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.heading = Label(
            text="[b]Scan your QR Code[/b]",
            markup=True,
            font_size=26,
            color=get_color_from_hex("#22223bff"),
            size_hint=(None, None),
            size=(400, 50),
            pos_hint={"center_x": 0.5, "top": 0.92}
        )
        self.add_widget(self.heading)

        self.scan_btn = Button(
            text="Scan QR Code",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.75},
            background_color=get_color_from_hex("#4ea8deff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.scan_btn.bind(on_press=lambda inst: App.get_running_app().start_scan_thread())
        self.add_widget(self.scan_btn)

        self.view_attendance_btn = Button(
            text="View Attendance",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.62},
            background_color=get_color_from_hex("#62AFE2FF"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.view_attendance_btn.bind(on_press=lambda inst: App.get_running_app().show_student_attendance_screen())
        self.add_widget(self.view_attendance_btn)

        self.back_btn = Button(
            text="Logout",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.49},
            background_color=get_color_from_hex("#adb5bdff"),
            color=get_color_from_hex("#22223bff"),
            bold=True,
            background_normal=""
        )
        self.back_btn.bind(on_press=lambda inst: App.get_running_app().logout_to_login())
        self.add_widget(self.back_btn)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos


class TeacherDashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(rgba=get_color_from_hex("#f0f4f8ff"))
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        self.class_id_label = Label(
            text="Teacher Dashboard",
            font_size=26,
            markup=True,
            color=get_color_from_hex("#22223bff"),
            size_hint=(None, None),
            size=(400, 50),
            pos_hint={"center_x": 0.5, "top": 0.92}
        )
        self.add_widget(self.class_id_label)

        self.qr_image = KivyImage(
            size_hint=(None, None),
            size=(200, 200),
            pos_hint={"center_x": 0.5, "top": 0.75}
        )
        self.add_widget(self.qr_image)

        gen_btn = Button(
            text="Generate QR",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.55},
            background_color=get_color_from_hex("#488155ff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        gen_btn.bind(on_press=lambda inst: App.get_running_app().generate_qr_current_class())
        self.add_widget(gen_btn)

        view_attendance_btn = Button(
            text="View Attendance",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.42},
            background_color=get_color_from_hex("#488155ff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        view_attendance_btn.bind(on_press=lambda inst: App.get_running_app().show_teacher_attendance_screen())
        self.add_widget(view_attendance_btn)

        back_btn = Button(
            text="Logout",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.29},
            background_color=get_color_from_hex("#adb5bdff"),
            color=get_color_from_hex("#22223bff"),
            bold=True,
            background_normal=""
        )
        back_btn.bind(on_press=lambda inst: App.get_running_app().logout_to_login())
        self.add_widget(back_btn)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos


class AttendanceViewScreen(Screen):
    """
    Generic screen to show a full CSV in a scrollable grid (teacher view).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.container = BoxLayout(orientation="vertical", padding=10, spacing=10)
        back_btn = Button(text="Back", size_hint=(1, 0.1))
        back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("teacher_dashboard"))
        self.container.add_widget(back_btn)

        self.scroll = ScrollView(size_hint=(1, 0.9))
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.container.add_widget(self.scroll)

        self.add_widget(self.container)

    def populate_from_csv(self, df):
        """
        Create a header row and then a label per CSV row.
        """
        self.grid.clear_widgets()
        # header
        header_layout = GridLayout(cols=len(df.columns), size_hint_y=None, height=30)
        for col in df.columns:
            header_layout.add_widget(Label(text=str(col)))
        self.grid.add_widget(header_layout)

        # rows
        for _, row in df.iterrows():
            row_layout = GridLayout(cols=len(df.columns), size_hint_y=None, height=28)
            for val in row:
                row_layout.add_widget(Label(text=str(val)))
            self.grid.add_widget(row_layout)


class StudentAttendanceScreen(Screen):
    """
    Screen to display a single student's attendance as two-column grid (subject, value)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)
        self.title_label = Label(text="Attendance", font_size=20, size_hint=(1, 0.1))
        layout.add_widget(self.title_label)

        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=2, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        layout.add_widget(self.scroll)

        back_btn = Button(text="Back", size_hint=(1, 0.1))
        back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("student_dashboard"))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def populate_for_student(self, student_name):
        """
        Read CSV, find the row and populate subject/value pairs.
        """
        self.grid.clear_widgets()
        try:
            df = pd.read_csv(CSV_FILE)
            if student_name not in df["Name"].values:
                App.get_running_app().popup("Error", "Attendance record not found!")
                return
            student_attendance = df[df["Name"] == student_name].drop(columns=["Name"])
            subjects = list(student_attendance.columns)
            values = student_attendance.iloc[0].values
            for s, v in zip(subjects, values):
                self.grid.add_widget(Label(text=str(s)))
                self.grid.add_widget(Label(text=str(v)))
            self.title_label.text = f"Attendance - {student_name}"
        except Exception as e:
            App.get_running_app().popup("Error", f"Failed to load attendance: {e}")


# ---------- App class tying everything together ----------
class AttendanceApp(App):
    def build(self):
        ensure_attendance_csv()  # <-- Add this line
        # Optional: set default window size similar to your Tkinter geometry
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
        """
        Called from TeacherDashboardScreen -> Generate QR button.
        Uses same qrcode logic as original and then updates Kivy Image widget source.
        """
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

        # Resize via PIL (not strictly necessary but keeps parity with Tkinter resizing)
        try:
            pil_img = PILImage.open(img_path)
            pil_img.thumbnail((200, 200))
            pil_img.save(img_path)
        except Exception:
            pass

        # Update Kivy Image widget on teacher dashboard
        t_screen = self.sm.get_screen("teacher_dashboard")
        t_screen.qr_image.source = img_path
        t_screen.qr_image.reload()
        self.popup("Success", f"QR generated for {class_id}")

    # ---------------- QR scanning (uses same OpenCV/pyzbar code but runs in a thread) ----------------
    def start_scan_thread(self):
        """
        Launch the blocking OpenCV capture/scan loop in a separate thread so the Kivy UI stays responsive.
        This keeps the scanning logic identical to your original scan_qr(), which used cv2.imshow in a loop.
        """
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
            # pass result back to main thread for UI update & attendance logic
            self.process_scan_result(class_id)
        else:
            self.popup("Error", "No QR code detected or scan cancelled.")

    @mainthread
    def process_scan_result(self, class_id):
        """
        Run the same post-scan logic as original: verify subject, check WiFi SSID, update CSV.
        """
        if class_id and class_id in SUBJECTS:
            wifi_ssid = get_wifi_ssid()
            if wifi_ssid == EXPECTED_WIFI:
                if update_attendance(self.student_name, class_id):
                    self.popup("Success", f"Attendance marked for {class_id}")
                    # self.logout_to_login()  # <-- Remove or comment out this line
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


if __name__ == "__main__":
    AttendanceApp().run()

# To install the required packages, run the following command:
# pip install kivy opencv-python pyzbar pillow pandas qrcode
