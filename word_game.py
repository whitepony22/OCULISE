from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.core.window import Window
from kivy.clock import Clock
import random
from camera_widget import CameraWidget, Notification
from chat_widget import RoundedButton
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import ListProperty, ObjectProperty, NumericProperty
from kivy.storage.jsonstore import JsonStore
import nltk
from nltk.corpus import wordnet

class WordGame(Screen):
    streak = NumericProperty(0) 
    highest_streak = NumericProperty(0)
    alphabet=ListProperty(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    background_color = ObjectProperty((141/255, 102/255, 142/255, 1))  #8d668e
    game_area_bgcolor = ObjectProperty((121/255, 82/255, 122/255, 1))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.streak = 0
        self.words = self.load_words("words.txt")
        self.word_buttons = []
        self.letter_buttons = []
        self.tries = 6
        self.current_letter_index = -1
        self.score_image = None
        self.selected_row, self.selected_col = 0, 0
        self.new_high_score_displayed = False

    def on_enter(self):
        Window.bind(on_key_down=self.on_key_down)
        CameraWidget.game_mode = True
        CameraWidget.camera_layout.pos_hint = {"y": 0, "right": 1}
        CameraWidget.gamemode_icon.source = 'Images/GAME_ACTIVE.png'
        self.streak = 0  # Reset score when starting
        self.new_high_score_displayed = False
        # Load high score from storage
        self.store = JsonStore('highscore.json')
        self.highest_streak = self.store.get('word')['high'] if self.store.exists('word') else 0
        if not self.letter_buttons:
            for letter in self.alphabet:
                btn = Button(text=letter,
                             font_size=18,
                             size_hint=(0.07, 0.1))
                            #  size_hint=(None, None),
                            #  size=(55, 55))
                self.letter_buttons.append(btn)
                self.ids.letter_grid.add_widget(btn)
        self.start_new_game()

    def on_leave(self):
        Window.unbind(on_key_down=self.on_key_down)
        CameraWidget.gamemode_icon.source = 'Images/DEFAULT.png'

    def start_new_game(self):
        """Resets the game with a new word."""
        self.word = random.choice(self.words)
        self.display_word = ["_" for _ in self.word]
        self.tries = 6
        self.ids.hangman.source = f"Images/HANGMAN_0.png"

        synsets = wordnet.synsets(self.word.lower())  # Ensure lowercase lookup
        self.hint = synsets[0].definition() if synsets else "No hint available"

        self.reveal_random_letters()
        self.current_letter_index = next((i for i, letter in enumerate(self.display_word) if letter == "_"), -1)
        self.ids.word_layout.clear_widgets()
        self.word_buttons.clear()

        for letter in self.display_word:
            btn = RoundedButton(
                text=letter,
                font_size=40,
                size_hint=(1, None),
                height=70,
                # size=(50, 50),
                background_color=(0, 0, 0, 0),  # Transparent background
                background_normal=''  # No background image
            )
            # Apply unique canvas properties to each button
            with btn.canvas.before:
                btn.color_instruction = Color(1, 1, 1, 0.4)
                btn.rounded_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[6])
            # Ensure the RoundedRectangle follows button size/pos
            btn.bind(size=self.update_rounded_rect, pos=self.update_rounded_rect)

            self.word_buttons.append(btn)
            self.ids.word_layout.add_widget(btn)

        self.update_display()
        self.update_selection()

        self.ids.hint_label.text = f"Hint: {self.hint}"

    def update_rounded_rect(self, instance, value):
        """Update the position and size of the button's rounded rectangle."""
        instance.rounded_rect.pos = instance.pos
        instance.rounded_rect.size = instance.size

    def load_words(self, filename):
        try:
            with open(filename, 'r') as file:
                words = file.read().splitlines()
            # Filter words with more than 4 letters and ensure they are alphabetic
            return [word.upper() for word in words if len(word) > 4 and word.isalpha()]
        except FileNotFoundError:
            print(f"File {filename} not found.")
            return []
        
    def reveal_random_letters(self):
        """Reveal 2 random letters."""
        if len(self.word) <= 6:
            num_revealed = 2
        elif len(self.word) <= 9:
            num_revealed = 3
        else:
            num_revealed = random.randint(4, 5)
        revealed_positions = random.sample(range(len(self.word)), num_revealed)
        for pos in revealed_positions:
            self.display_word[pos] = self.word[pos]

    def eye_navigation(self, dt = None):
        if CameraWidget.direction:
            direction = CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None

    def on_key_down(self, instance, key, *args):
        key_mapping = {273: "up", 274: "down", 275: "right", 276: "left", 32: "Space"}
        if key in key_mapping:
            self.navigate_action(key_mapping[key])

    def navigate_action(self, direction):
        rows, cols = 2, 13
        total_letters = len(self.alphabet)
        if self.manager.current != 'word' or not Notification.is_active:
            if not CameraWidget.game_mode:
                if direction == "up":
                    self.manager.current = 'option'
                elif direction == 'right':
                    self.start_new_game()
                    # CameraWidget.game_mode = True
            else:
                if direction == "right":
                    self.selected_col = (self.selected_col + 1) % cols
                elif direction == "left":
                    self.selected_col = (self.selected_col - 1) % cols
                elif direction == "down":
                    # Toggle between row 0 and row 1 within the same column
                    self.selected_row = 1 if self.selected_row == 0 else 0
                elif direction == "up":
                    self.confirm_letter()
                elif direction == "Space":
                    CameraWidget.game_mode = not CameraWidget.game_mode
                # Ensure selection remains within bounds
                selected_index = self.selected_row * cols + self.selected_col
                if selected_index >= total_letters:
                    self.selected_row = (total_letters - 1) // cols
                    self.selected_col = (total_letters - 1) % cols
                self.update_selection()

    def update_selection(self):
        """Highlight selected letter in the grid."""
        for btn in self.letter_buttons:
            btn.background_color = (1, 1, 1, 1)
        selected_index = self.selected_row * 13 + self.selected_col
        if selected_index < len(self.alphabet):
            self.letter_buttons[selected_index].background_color = (141/255, 102/255, 142/255, 1)  #8d668e

    def confirm_letter(self):
        """Place selected letter in the word."""
        selected_index = self.selected_row * 13 + self.selected_col
        if selected_index >= len(self.alphabet) or self.current_letter_index == -1:
            return
        selected_letter = self.alphabet[selected_index]
        if selected_letter in self.word:
            # Correct guess
            for i, letter in enumerate(self.word):
                if letter == selected_letter:
                    self.display_word[i] = selected_letter
                    self.word_buttons[i].text = selected_letter
            # Move to next blank letter
            remaining_blanks = [i for i, letter in enumerate(self.display_word) if letter == "_"]
            self.current_letter_index = remaining_blanks[0] if remaining_blanks else -1
        else:
            # Wrong guess
            self.tries -= 1
        self.update_display()
        if "_" not in self.display_word:
            self.ids.tries_label.text = f""
            self.streak += 1
            if self.streak > self.highest_streak:
                self.highest_streak = self.streak
                if not self.new_high_score_displayed:
                    self.display_score_image('high')
                    self.ids.hangman.source = f"Images/DEFAULT.png"
                    self.new_high_score_displayed = True
                else:
                    self.display_score_image('win')
                    self.ids.hangman.source = f"Images/DEFAULT.png"
                self.store.put('word', high=self.highest_streak)  # Save new high score
            else:
                self.display_score_image('win')  # Show win animation
                self.ids.hangman.source = f"Images/DEFAULT.png"
            Clock.schedule_once(lambda dt: self.start_new_game(), 5)
        elif self.tries == 0:
            self.streak = 0  # Reset streak on loss
            self.ids.tries_label.text = f"Word: {self.word}"
            self.display_score_image('lose')  # Show win animation
            Clock.schedule_once(lambda dt: self.start_new_game(), 5)

    def update_display(self):
        """Update UI elements."""
        self.ids.tries_label.text = f"Tries Left: {self.tries}"
        if self.tries >= 0:
            self.ids.hangman.source = f"Images/HANGMAN_{6 - self.tries}.png"

    def display_score_image(self, outcome):
        # Remove existing image if it exists
        if self.score_image:
            self.remove_widget(self.score_image)
        # Select the image based on the outcome
        if outcome == 'win':
            img_source = "Images/WORD_WIN.gif"
            new_color = (159/255, 135/255, 163/255, 1) #9f87a3
            # new_game_area_color = (139/255, 115/255, 143/255, 1)
        elif outcome == 'lose':
            img_source = "Images/WORD_LOSE.gif"
            new_color = (84/255, 84/255, 84/255, 1) #545454
            # new_game_area_color = (64/255, 64/255, 64/255, 1)
        elif outcome == 'high':
            img_source = "Images/HIGHEST_STREAK.gif"
            new_color = (0.2745, 0.1216, 0.2784, 1) # dark purple
        # Change the background color with animation
        Animation(background_color=new_color, duration=1).start(self)
        Animation(game_area_bgcolor=new_color, duration=1).start(self)
        # Display win/lose image
        self.score_image = Image(source=img_source, size_hint=(1, 1),
                                pos_hint={'center_x': 0.4, 'center_y': 0.5}, opacity=1)
        self.add_widget(self.score_image)
        # Schedule fade-out after 2 seconds
        Clock.schedule_once(self.fade_out_score_image, 4)

    def fade_out_score_image(self, *args):
        if self.score_image:
            fade_out = Animation(opacity=0, duration=1)
            fade_out.bind(on_complete=lambda *x: self.remove_score_image())
            fade_out.start(self.score_image)

    def remove_score_image(self):
        if self.score_image:
            self.remove_widget(self.score_image)
            self.score_image = None
        # Reset to the default color
        Animation(background_color=(141/255, 102/255, 142/255, 1), duration=1).start(self)
        Animation(game_area_bgcolor=(121/255, 82/255, 122/255, 1), duration=1).start(self)