from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.app import App


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
        """Create a header row and then a label per CSV row."""
        self.grid.clear_widgets()
        header_layout = GridLayout(cols=len(df.columns), size_hint_y=None, height=30)
        for col in df.columns:
            header_layout.add_widget(Label(text=str(col)))
        self.grid.add_widget(header_layout)

        for _, row in df.iterrows():
            row_layout = GridLayout(cols=len(df.columns), size_hint_y=None, height=28)
            for val in row:
                row_layout.add_widget(Label(text=str(val)))
            self.grid.add_widget(row_layout)
