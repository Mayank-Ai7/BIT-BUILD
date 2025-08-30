from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App
from kivy.graphics import Rectangle
from kivy.utils import get_color_from_hex


class AttendanceViewScreen(Screen):
    """
    Screen to show attendance data from PostgreSQL database in a scrollable grid (teacher view).
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Background
        with self.canvas.before:
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_bg_rect, pos=self._update_bg_rect)
        
        self.container = BoxLayout(orientation="vertical", padding=10, spacing=10)
        
        # Title
        self.title = Label(
            text="Class Attendance Overview",
            size_hint=(1, 0.1),
            color=(0, 0, 0, 1),
            font_size='20sp',
            bold=True
        )
        self.container.add_widget(self.title)
        
        # Scrollable content
        self.scroll = ScrollView(size_hint=(1, 0.8))
        self.grid = GridLayout(cols=1, size_hint_y=None, spacing=(0, 10))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.container.add_widget(self.scroll)
        
        # Back button
        back_btn = Button(
            text="Back",
            size_hint=(1, 0.1),
            background_normal="",
            background_color=get_color_from_hex("#62AFE2FF"),
            color=get_color_from_hex("#FFFFFFFF"),
            bold=True
        )
        back_btn.bind(on_press=lambda inst: App.get_running_app().go_to_screen("teacher_dashboard"))
        self.container.add_widget(back_btn)

        self.add_widget(self.container)

    def _update_bg_rect(self, *args):
        self.bg_rect.size = self.size
        self.bg_rect.pos = self.pos

    def populate_from_database(self, attendance_data):
        """
        Create a grid layout showing attendance data from database.
        attendance_data should be a list of tuples (student_name, subject_name, attendance_count)
        """
        self.grid.clear_widgets()
        
        # Create header
        header_layout = GridLayout(
            cols=3,  # student, subject, count
            size_hint_y=None,
            height=40,
            spacing=(10, 0)
        )
        
        headers = ["Student", "total_classes_attended", "attendance_percentage"]
        for header in headers:
            header_layout.add_widget(
                Label(
                    text=header,
                    color=(0, 0, 0, 1),
                    font_size='16sp',
                    bold=True
                )
            )
        self.grid.add_widget(header_layout)

        # Create rows for attendance data
        current_student = None
        for student_name, total_classes_attended, attendance_percentage in attendance_data:
            row_layout = GridLayout(
                cols=3,
                size_hint_y=None,
                height=35,
                spacing=(10, 0)
            )
            
            # Add student name
            row_layout.add_widget(
                Label(
                    text=str(student_name),
                    color=(0, 0, 0, 1),
                    font_size='14sp'
                )
            )
            
            # Add subject name
            row_layout.add_widget(
                Label(
                    text=int(total_classes_attended),
                    color=(0, 0, 0, 1),
                    font_size='14sp'
                )
            )
            
            # Add attendance count
            row_layout.add_widget(
                Label(
                    text=int(attendance_percentage),
                    color=(0, 0, 0, 1),
                    font_size='14sp'
                )
            )
            
            self.grid.add_widget(row_layout)