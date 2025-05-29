from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button

class KeyboardWidget(FloatLayout):
    def __init__(self, **kwargs):
        super(KeyboardWidget, self).__init__(**kwargs)
        self.opacity = 0

    def show(self):
        """Show the keyboard"""
        self.opacity = 1  # Make visible
        print("Available ids:", self.ids.keys())  # Debugging
        self.populate_letters()
        self.populate_numbers()
        self.populate_special_chars()
        self.populate_delete()

    def hide(self):
        """Hide the keyboard"""
        self.opacity = 0
        self.ids.am_letters_layout.clear_widgets()
        self.ids.nz_letters_layout.clear_widgets()
        self.ids.numbers_layout.clear_widgets()
        self.ids.special_chars_layout.clear_widgets()
        self.ids.delete_layout.clear_widgets()

    def populate_letters(self):
        letters_am = "ABCDEFGHIJKLM"
        letters_nz = "NOPQRSTUVWXYZ"
        for letter in letters_am:
            self.ids.am_letters_layout.add_widget(Button(text=letter))
        for letter in letters_nz:
            self.ids.nz_letters_layout.add_widget(Button(text=letter))
    
    def populate_numbers(self):
        for num in range(10):
            self.ids.numbers_layout.add_widget(Button(text=str(num)))
    
    def populate_special_chars(self):
        special_chars = ["Space", "Enter", ".", "!", "?", ",", "'", "&"]
        for char in special_chars:
            self.ids.special_chars_layout.add_widget(Button(text=char))
        
        caps_lock = Button(text="Caps Lock", size_hint_y=0.5)
        word_pred = Button(text="Word Prediction", size_hint_y=0.5)
        self.ids.special_chars_layout.add_widget(caps_lock)
        self.ids.special_chars_layout.add_widget(word_pred)
    
    def populate_delete(self):
        for action in ["Clear", "Backspace", "Undo"]:
            self.ids.delete_layout.add_widget(Button(text=action))