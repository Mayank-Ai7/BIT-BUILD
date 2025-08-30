from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.utils import get_color_from_hex
from kivy.app import App


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # --- Background image ---
        with self.canvas.before:
            self.bg_rect = Rectangle(source="bg2.png", size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)

        # --- Main vertical layout ---
        layout = BoxLayout(
            orientation="vertical",
            spacing=30,
            padding=[50, 50, 50, 50],  # Less top padding to keep heading visible
        )

        # --- Heading at top ---
        self.heading = Label(
            text="[b]Attendance System[/b]",
            markup=True,
            font_size="40sp",
            color=get_color_from_hex("#1E48A8D3"),  # bright yellow
            size_hint=(1, None),
            height=80,
            halign="center",
            valign="middle"
        )
        layout.add_widget(self.heading)

        # Add a spacer BoxLayout to push buttons to center
        layout.add_widget(BoxLayout(size_hint_y=1))

        # --- Student Login Button ---
        self.btn_student = Button(
            text="Student Login",
            font_size=22,
            size_hint=(1, None),
            height=70,
            background_normal="",
            background_color=get_color_from_hex("#62AFE2FF"),
            color=get_color_from_hex("#FFFFFFFF"),
            bold=True
        )
        with self.btn_student.canvas.before:
            Color(rgba=get_color_from_hex("#62AFE2FF"))
            self.student_rect = RoundedRectangle(
                size=self.btn_student.size,
                pos=self.btn_student.pos,
                radius=[30, 30, 30, 30]
            )
        self.btn_student.bind(size=self._update_student_btn, pos=self._update_student_btn)
        self.btn_student.bind(on_press=lambda inst: App.get_running_app().go_to_screen("student_login"))
        layout.add_widget(self.btn_student)

        # --- Teacher Login Button ---
        self.btn_teacher = Button(
            text="Teacher Login",
            font_size=22,
            size_hint=(1, None),
            height=70,
            background_normal="",
            background_color=get_color_from_hex("#488155FF"),
            color=get_color_from_hex("#FFFFFFFF"),
            bold=True
        )
        with self.btn_teacher.canvas.before:
            Color(rgba=get_color_from_hex("#488155FF"))
            self.teacher_rect = RoundedRectangle(
                size=self.btn_teacher.size,
                pos=self.btn_teacher.pos,
                radius=[30, 30, 30, 30]
            )
        self.btn_teacher.bind(size=self._update_teacher_btn, pos=self._update_teacher_btn)
        self.btn_teacher.bind(on_press=lambda inst: App.get_running_app().go_to_screen("teacher_login"))
        layout.add_widget(self.btn_teacher)

        # Add another spacer to balance vertical centering
        layout.add_widget(BoxLayout(size_hint_y=1))

        self.add_widget(layout)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def _update_student_btn(self, *args):
        self.student_rect.size = self.btn_student.size
        self.student_rect.pos = self.btn_student.pos

    def _update_teacher_btn(self, *args):
        self.teacher_rect.size = self.btn_teacher.size
        self.teacher_rect.pos = self.btn_teacher.pos