from kivy.uix.boxlayout import BoxLayout

class EmergencyWidget(BoxLayout):
    
    def __init__(self, **kwargs):
        super(EmergencyWidget, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.opacity = 0  # Start hidden

    def show(self):
        self.opacity = 1  # Make visible

    def hide(self):
        self.opacity = 0  # Make hidden
