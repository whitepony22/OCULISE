from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.properties import BooleanProperty, NumericProperty
from kivy.uix.button import Button
from kivy.uix.image import Image


class FileWidget(FloatLayout):
    is_file_visible = BooleanProperty(False)  # Controls visibility
    current_index = NumericProperty(0)  # Tracks the start index for displaying buttons
    selected_index = NumericProperty(0)  # Tracks the highlighted button within the displayed buttons
    
    def __init__(self, **kwargs):
        super(FileWidget, self).__init__(**kwargs)
        self.entries = []  # Store list of entries from file
        self.opacity = 0  # Start hidden
        self.buttons = []
        self.row = 9

        # Create GridLayout for buttons (2 columns, 3 rows)
        self.button_layout = GridLayout(
            cols=1, rows=self.row, size_hint=(0.3, 0.5), pos_hint={'left': 1, 'top': 0.8}, padding = 8, spacing = 8
        )
        self.add_widget(self.button_layout)

    def update_file_display(self):
        """Update the displayed list of buttons."""
        file_path = "C:/Program Files/Python312/Main Project/Interface/OCULISE/K_Kivy12.6 (Chat)/typed_content.txt"
        try:
            with open(file_path, 'r') as file:
                content = file.read()
                self.entries = [entry.strip() for entry in content.split("\n---\n") if entry.strip()]
                print(self.entries)
        except FileNotFoundError:
            print(f"Error: The file at {file_path} was not found.")
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            return

        self.refresh_buttons()

    def update_basic_phrases_display(self):
        """Update the displayed list of buttons to show basic phrases."""
        self.entries = ['yes', 'no', 'hello', 'water', 'hungry', 'medicine', 'sleepy', 'pain', 'TV', 'I\'m fine', 'Thank you', 'Bye', 'Sorry', 'Help']
        self.refresh_buttons()

    def refresh_buttons(self):
        """Refresh the displayed buttons based on current index."""
        self.button_layout.clear_widgets()
        if hasattr(self,'highlight_layout') and hasattr(self, 'select_image') and self.select_image in self.highlight_layout.children:
            self.highlight_layout.remove_widget(self.select_image)
            self.highlight_layout.remove_widget(self.delete_image)
        self.buttons = []
        
        end_index = self.current_index + self.row  # Display up to self.row buttons
        self.visible_entries = self.entries[self.current_index:end_index]
        # print('Visible entries:', self.visible_entries)

        for i, entry in enumerate(self.visible_entries):
            # Split the entry into words
            words = entry.split()
            # Take the first three words and add "..." if more words exist
            display_text = ' '.join(words[:4]) + (' ...' if len(words) > 3 else '')
            button = Button(text = display_text, size_hint_y = None, height = 50)
            button.bind(on_press = self.on_button_press)
            self.button_layout.add_widget(button)
            self.buttons.append(button)

        self.update_highlight()

    def update_highlight(self):
        """Update the button highlight based on selected index."""
        # print(f"Updating highlight: current_index={self.current_index}, selected_index={self.selected_index}")

        # If no buttons exist, return
        if not self.buttons:
            return
        
        if self.selected_index == -1:
            if hasattr(self,'highlight_layout') and hasattr(self, 'select_image') and self.select_image in self.highlight_layout.children:
                self.highlight_layout.remove_widget(self.select_image)
                self.highlight_layout.remove_widget(self.delete_image)
            return

        # Ensure selected index is within range
        if self.selected_index < 0 or self.selected_index >= len(self.buttons):
            return

        # Create FloatLayout once if it doesn’t exist
        if not hasattr(self, 'highlight_layout'):
            self.highlight_layout = FloatLayout(size_hint=(None, None), size=(self.buttons[0].width, 60))
            self.add_widget(self.highlight_layout)
        if not hasattr(self,'delete_image'):
            # Add images to the FloatLayout
            self.delete_image = Image(source='Images/DELETE.png', size_hint=(None, None), size=(30, 30), pos_hint={'x': 0.01, 'center_y': 0.5})
        if not hasattr(self,'select_image'):    
            self.select_image = Image(source='Images/SELECT.png', size_hint=(None, None), size=(30, 30), pos_hint={'x': 0.89, 'center_y': 0.5})
            
        if self.delete_image not in self.highlight_layout.children:
            self.highlight_layout.add_widget(self.delete_image)
        if self.select_image not in self.highlight_layout.children:
            self.highlight_layout.add_widget(self.select_image)

        # Move the FloatLayout to the highlighted button
        self.button_layout.do_layout()
        selected_button = self.buttons[self.selected_index]
        if self.selected_index == 0:
                # Special case for the first button (ensure correct positioning)
            self.highlight_layout.pos = self.buttons[0].pos
        else:
            self.highlight_layout.pos = selected_button.pos  # Move FloatLayout to button's position
        self.highlight_layout.size = (selected_button.width, selected_button.height)

        # Update button styles
        for i, button in enumerate(self.buttons):
            if i == self.selected_index:
                button.background_color = (0, 0.6, 0, 1)  # Highlighted (Blue)
                button.height = 60  # Increase height for highlighted button
            else:
                button.background_color = (1, 1, 1, 1)  # Default (White)
                button.height = 50  # Reset height for other buttons

    def get_highlighted_text(self):
        """Return the text of the currently highlighted button."""
        if 0 <= self.selected_index < len(self.buttons):
            return self.visible_entries[self.selected_index]
        return None  # Return None if no button is highlighted

    def on_button_press(self, instance):
        """Handle button press event."""
        print(f"Button pressed: {instance.text}")
    
    def move_selection_down(self):
        """Move selection down, scrolling smoothly, with wrap-around navigation."""
        self.ids.save_button.source = 'Images/SAVE_DEFAULT.png'
        if self.selected_index < len(self.buttons) - 1:
            # Move within the visible buttons
            self.selected_index += 1
        elif self.current_index + self.selected_index + 1 < len(self.entries):
            # Scroll down by shifting the window
            self.current_index += 1
            self.selected_index = self.row - 1
            self.refresh_buttons()
        else:
            # Wrap around to the first button
            self.current_index = 0
            self.selected_index = 0
            self.refresh_buttons()

        self.update_highlight()

    def move_selection_up(self):
        """Move selection up, scrolling smoothly when needed."""
        if self.selected_index > 0:
            # Move within the visible buttons
            self.selected_index -= 1
        elif self.current_index > 0:
            # Scroll up by shifting the window
            self.current_index -= 1
            # self.selected_index = self.row - 1  # Move to the last button in the new set
            self.refresh_buttons()  # Re-render buttons to reflect new positions

        self.update_highlight()

    def scroll_down(self):
        """Scroll down if there are more buttons to display."""
        if self.current_index + self.row < len(self.entries):
            self.current_index += self.row
            self.refresh_buttons()
        self.update_highlight()
