from kivy.uix.textinput import TextInput
import alphabet_detection
from camera_widget import CameraWidget, AlertPopup
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.core.window import Window
from word_prediction import predict_with_bert
from kivy.properties import ObjectProperty, NumericProperty, StringProperty

class TypingWidget(TextInput):

    caps = NumericProperty(1)  # Declare caps as a NumericProperty
    prediction_width = NumericProperty(0)
    # window_height = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.arrow_mapping = {
            # 273: "↑",  # Up arrow
            # 274: "↓",  # Down arrow
            # 275: "→",  # Right arrow
            # 276: "←",  # Left arrow
            'Up': "↑",  # Up arrow
            'Down': "↓",  # Down arrow
            'Right': "→",  # Right arrow
            'Left': "←",  # Left arrow
        }
        self.directions = []  # Stores the sequence of arrows

        self.predictions = []  # List of predictions
        self.selected_index = 0  # Index of the currently selected prediction
        self.prediction_active = False  # Whether in prediction mode
        self.prediction_width = 0

        self.undo_stack = []  # Stack to store undo information

        self.word_hint = ''
        self.word_prediction_mode = False  # Flag to indicate word prediction mode

        self.parent_screen = ObjectProperty(None)

        # Bind to the window resize event
        Window.bind(on_resize=self.on_window_resize)

        self.bind(focus=self.on_focus_change)

    def on_focus_change(self, instance, value):
        if not value:
            Window.bind(on_key_down=self.parent_screen.on_key_down)

    def on_window_resize(self, window, width, height):
        """Handle window resize event."""
        # print(f"Window resized to: {width}x{height}")
        TypingWidget.window_height = height

    def on_cursor(self, instance, value):
        print(f"Cursor changed to: {value}")
        # Call the parent class's method to maintain default behavior
        print(self.directions)
        super().on_cursor(instance, value)

    def typing_navigate_action(self, direction):
        """Handle navigation based on eye direction from CameraWidget."""
        print('On type mode:', CameraWidget.type_mode)
        if self.prediction_active:
            self.prediction_navigation(direction)
        else:
            if direction in self.arrow_mapping:
                print("Typing the arrow", direction)
                arrow = self.arrow_mapping[direction]
                self.directions.append(arrow)
                self.insert_text(arrow)  # Append arrow to the TextInput
                pattern_length = len(self.directions)
                if self.cursor[0] == pattern_length or (self.cursor[0] > (pattern_length + 1) and self.text[self.cursor[0] - (pattern_length + 1)] == ' ' and self.text[self.cursor[0] - (pattern_length + 2)] in ['.', '!', '?']):
                    caps = 0
                elif self.caps == 0:  # Check for pattern match with 1 (after the sentence starts)
                    caps = 0
                else:
                    caps = 1
                self.check_pattern(caps)
                
                def move_cursor(dt):
                    self.do_cursor_movement('cursor_right')
                Clock.schedule_once(move_cursor, 0.05)  # Delay cursor movement slightly for the error with left arrow

    def prediction_navigation(self, direction):
        """Handle navigation and selection based on key input."""
        if not CameraWidget.type_mode:
            self.parent_screen.navigate_action(dt=0)
            print(self.parent_screen)
            return
        if (direction == 'Right') and self.selected_index < len(self.predictions) - 1:
            self.selected_index += 1
            self.highlight_prediction(self.selected_index)
        elif (direction == 'Left') and self.selected_index > 0:
            self.selected_index -= 1
            self.highlight_prediction(self.selected_index)
        elif (direction == 'Up') :  # Select the current prediction
            selected_prediction = self.predictions[self.selected_index]
            self.delete_text(len(self.directions))
            if self.word_prediction_mode: # Clear the word hint
                self.delete_text(len(self.word_hint))  # Deleting the length of word hint
                self.word_hint = ''
            self.insert_text(selected_prediction)
            self.directions.clear()
            self.exit_prediction_mode()
            print('Selected prediction:', selected_prediction, 'directions:', self.directions)
        elif (direction == 'Down') :  # Exit prediction mode
            # if self.word_hint:
            #     self.insert_text(self.word_hint)
            #     self.word_hint = ''
            self.exit_prediction_mode()

    def check_pattern(self, caps):
  
        if len(self.directions) in {2, 3, 4}:  # Trigger based on directions length
            predictions = alphabet_detection.get_predictions(self.directions, caps)

            # Handle predictions for all valid lengths
            if predictions:
                if len(self.directions) < 4:
                    self.update_predictions(predictions)
                elif len(self.directions) == 4:  # Complete a detected pattern
                    detected_char = alphabet_detection.detect_alphabet(self.directions, caps)
                    if detected_char:
                        self.delete_text(4)
                        self.insert_text(detected_char)
                    else:
                        AlertPopup(message="No combination found!").open()
                    self.directions.clear()

            # Custom actions for 2-arrow patterns
            elif len(self.directions) == 2:
                if self.directions == ['↓', '↓']:
                    self.delete_text(2)
                    self.directions.clear()
                    self.do_cursor_movement('cursor_down')
                elif self.directions == ['↑', '↑']:
                    self.delete_text(2)
                    self.directions.clear()
                    self.do_cursor_movement('cursor_up')
                elif self.directions == ['→', '→']:
                    self.delete_text(2)
                    self.directions.clear()
                    self.do_cursor_movement('cursor_right')
                elif self.directions == ['←', '←']:
                    self.delete_text(2)
                    self.directions.clear()
                    self.do_cursor_movement('cursor_left')

                elif self.directions == ['→', '↓']: # Word Prediction
                    self.delete_text(2)
                    self.directions.clear()
                    self.word_prediction_mode = True  # Set flag to indicate word prediction mode
                    self.word_prediction()

                elif self.directions == ['→', '←']: # Caps on/off
                    self.delete_text(2)
                    self.directions.clear()
                    self.caps = 0 if self.caps == 1 else 1

                elif self.directions == ['←', '↑']:  # Clear
                    self.clear_text()
                elif self.directions == ['←', '↓']:  # Delete Letter
                    self.delete_letter()
                elif self.directions == ['←', '→']:  # Undo
                    self.undo()

            else:
                self.delete_text(len(self.directions))
                AlertPopup(message="No combination found!").open()
                self.directions.clear()


    def insert_text(self, substring, from_undo=False):
        # Call the parent class method to insert the text at the cursor
        super().insert_text(substring, from_undo)

    def delete_text(self, length):
        for _ in range(length):
            self.do_backspace()

    def clear_text(self):
        """Handle delete word logic and save to undo stack."""
        self.delete_text(2)
        self.directions.clear()
        # Store entire text for undo
        deleted_text = self.text
        # Select all text
        self.select_all()
        # Delete selection
        self.delete_selection()
        # Save to undo stack
        self.undo_stack.append(("clear", self.cursor, deleted_text))
        # Reset prediction height
        # self.parent_screen.ids.prediction_scroll.height = TypingWidget.window_height - 200
        
    def delete_letter(self):
        """Handle delete letter logic and save to undo stack."""
        self.delete_text(2)
        self.directions.clear()
        if not self.text:
            print('Nothing to delete')
            deleted_letter =''
        elif len(self.text) == 2:
            deleted_letter = self.text[1]
            self.do_backspace()
        elif len(self.text) == 1:
            deleted_letter = self.text
            self.do_backspace()
        else:
            lines = self.text.split("\n")  # Split into lines
            line = lines[self.cursor[1]]
            # deleted_letter = line[self.cursor[0] - 1]
            if self.cursor[0] == 0:
                deleted_letter = '\n'  # Deleted newline at the start of the line
            else:
                deleted_letter = line[self.cursor[0] - 1]  # Normal character deletion
            self.do_backspace()
        print('The deleted letter:', deleted_letter)
        self.undo_stack.append(("letter", self.cursor[0], deleted_letter))  # Save type, position, and text

    def undo(self):
        """Undo the last deletion."""
        if not self.undo_stack:
            print("Nothing to undo!")
            self.delete_text(2)
            self.directions.clear() 
            return

        self.delete_text(2)
        self.directions.clear()
        print('Undo stack:', self.undo_stack)
        action_type, position, deleted_text = self.undo_stack.pop()
        self.insert_text(deleted_text)  # Restore the deleted word
        
    def word_prediction(self):
        """Check for word predictions"""
        lines = self.text.split("\n")  # Split into lines
        line = lines[self.cursor[1]]
            
        # Get partial word
        word_hint = ''
        cur_x = self.cursor[0]
        while cur_x > 0 and line[cur_x - 1] != ' ':
            word_hint = line[cur_x - 1] + word_hint
            cur_x -= 1  # Ensure progression to avoid infinite loop
        
        # Get prior context (previous few words before the current word)
        full_context = line[:cur_x]
        self.word_hint = word_hint

        # Get predictions using both the full sentence context and the word fragment
        suggestions = predict_with_bert(context=full_context.strip(), prefix=word_hint.lower())

        if suggestions:
            if word_hint.istitle():  # First letter capitalized (e.g., "Hello")
                suggestions = [s.capitalize() for s in suggestions]
            elif word_hint.isupper():  # All uppercase (e.g., "HELLO")
                suggestions = [s.upper() for s in suggestions]
            # Otherwise, keep them lowercase (default from BERT)
            self.update_predictions(suggestions)
        else:
            AlertPopup(message="No relevant suggestions found!").open()
            print("\nNo relevant suggestions found.")
            self.word_prediction_mode = False

    def update_predictions(self, predictions):
        """Update the prediction list in the horizontal ScrollView."""
        self.predictions = sorted(predictions)
        self.selected_index = 0  # Reset selection
        self.prediction_active = True
        prediction_layout = self.parent_screen.ids.prediction_layout
        print(self.parent_screen.ids)
        prediction_layout.clear_widgets()  # Clear existing predictions

        for prediction in sorted(predictions):

            if prediction == ' ':
                text = 'Space'
            elif prediction == '\n':
                text = 'Enter'
            else:
                text = prediction

            btn = Button(
                text=text,
                size_hint=(None, None),  # Disable automatic sizing
                size=(35 + (8 * (len(text) - 1)), 35),  # Adjust the width based on text
                font_size='15sp',
                background_color=(0.85, 0.92, 1, 1)  # Default button color
            )

            self.prediction_width += (35 + (8 * (len(text) - 1)) + 10)

            prediction_layout.add_widget(btn)

        # Highlight the first prediction by default
        self.highlight_prediction(0)

    def highlight_prediction(self, index):
        """Highlight the prediction at the given index."""
        prediction_layout = self.parent_screen.ids.prediction_layout
        for i, btn in enumerate(prediction_layout.children):
            if len(prediction_layout.children)-i-1 == index:
                btn.background_color = (0, 1, 0, 1)  # Highlight selected button
                button = prediction_layout.children[i]
                self.parent_screen.ids.prediction_scroll.scroll_to(button, padding=10)  # Scroll to the button with some padding
            else:
                btn.background_color = (0.85, 0.92, 1, 1)  # Default color

    def exit_prediction_mode(self):
        """Exit prediction mode and clear the prediction bar."""
        self.prediction_active = False
        self.parent_screen.ids.prediction_layout.clear_widgets()
        self.prediction_width = 0
        if self.word_prediction_mode: # Exit word prediction mode
            self.word_prediction_mode = False