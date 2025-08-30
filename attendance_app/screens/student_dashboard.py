from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Rectangle
from kivy.utils import get_color_from_hex
from kivy.app import App

class StudentDashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Background image ---
        with self.canvas.before:
            self.bg_rect = Rectangle(source="b3.png", size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # --- Heading ---
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

        # --- Scan Button ---
        self.scan_btn = Button(
            text="Scan QR Code",
            font_size=20,
            size_hint=(None, None),
            size=(320, 60),
            pos_hint={"center_x": 0.5, "top": 0.75},
            background_color=get_color_from_hex("#3eca9eff"),
            color=get_color_from_hex("#ffffffff"),
            bold=True,
            background_normal=""
        )
        self.scan_btn.bind(on_press=lambda inst: App.get_running_app().start_scan_thread())
        self.add_widget(self.scan_btn)

        # --- View Attendance Button ---
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

        # --- Logout Button ---
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

    # --- Background update on resize ---
    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos
