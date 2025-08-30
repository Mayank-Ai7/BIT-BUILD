import pandas as pd
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App
from kivy.graphics import Rectangle
from kivy.utils import get_color_from_hex

from utils.helpers import get_student_attendance

class StudentAttendanceScreen(Screen):
    """
    Screen to display a single student's attendance as two-column grid (subject, value)
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Background image ---
        with self.canvas.before:
            self.bg_rect = Rectangle(size=self.size, pos=self.pos, color=(1, 1, 1, 1))
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # --- Main layout ---
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Title label
        self.title_label = Label(
            text="Attendance",
            font_size=20,
            size_hint=(1, 0.1),
            color=get_color_from_hex("#22223bff")  # optional: color to make text visible on background
        )
        layout.add_widget(self.title_label)

        # Scrollable grid for attendance
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=2, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        layout.add_widget(self.scroll)

        # Back button
        back_btn = Button(
            text="Back",
            size_hint=(1, 0.1),
            background_normal="",
            background_color=get_color_from_hex("#62AFE2FF"),
            color=get_color_from_hex("#FFFFFFFF"),
            bold=True
        )
        back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("student_dashboard"))
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def populate_for_student(self, student_name):
        """Get attendance from database and populate grid"""
        self.grid.clear_widgets()
        self.grid.spacing = (0, 20)
        try:
            attendance_data = get_student_attendance(student_name)
            
            # Add headers
            subject_header = Label(
                text="Subject",
                color=(0, 0, 0, 1),
                font_size='18sp',
                bold=True,
                size_hint_y=None,
                height=40
            )
            count_header = Label(
                text="Attended",
                color=(0, 0, 0, 1),
                font_size='18sp',
                bold=True,
                size_hint_y=None,
                height=40
            )
            self.grid.add_widget(subject_header)
            self.grid.add_widget(count_header)

            # Add attendance data
            for class_name, count in attendance_data:
                subject_label = Label(
                    text=str(class_name),
                    color=(0, 0, 0, 1),
                    font_size='16sp',
                    size_hint_y=None,
                    height=40
                )
                value_label = Label(
                    text=str(count),
                    color=(0, 0, 0, 1),
                    font_size='16sp',
                    size_hint_y=None,
                    height=40
                )
                self.grid.add_widget(subject_label)
                self.grid.add_widget(value_label)
            
            self.title_label.text = f"Attendance - {student_name}"
        except Exception as e:
            App.get_running_app().popup("Error", f"Failed to load attendance: {e}")