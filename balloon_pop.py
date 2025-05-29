from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
import random
from camera_widget import CameraWidget, Notification
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore

class BalloonPopGame(Screen):
    streak = NumericProperty(0) 
    highest_streak = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.streak = 0
        self.score_image = None
        self.positions = ['Center', 'Left', 'Right', 'Up', 'Down']
        self.current_position = None
        self.new_high_score_displayed = False
        
    def on_enter(self):
        Window.bind(on_key_down=self.on_key_down)
        CameraWidget.game_mode = True
        CameraWidget.camera_active = True
        CameraWidget.camera_layout.pos_hint = {"y": 0, "right": 1}
        CameraWidget.gamemode_icon.source = 'Images/GAME_ACTIVE.png'
        self.streak = 0
        self.new_high_score_displayed = False
        self.reposition_balloon()
        # Load high score from storage
        self.store = JsonStore('highscore.json')
        self.highest_streak = self.store.get('balloon')['high'] if self.store.exists('balloon') else 0

    def on_leave(self):
        Window.unbind(on_key_down=self.on_key_down)
        CameraWidget.game_mode = False
        CameraWidget.gamemode_icon.source = 'Images/DEFAULT.png'
    
    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def pop_balloon(self, *args):
        self.streak += 1
        if self.streak > self.highest_streak:
            self.highest_streak = self.streak
            self.store.put('balloon', high=self.highest_streak)  # Save new high score
            if not self.new_high_score_displayed:
                self.display_score_image()
                self.new_high_score_displayed = True
        anim = Animation(opacity=0, size=(120, 120), duration=0.2)
        anim.bind(on_complete=lambda *x: self.reset_balloon())
        anim.start(self.ids.balloon_image)
        # self.reposition_balloon()

    def reset_balloon(self):
        # Reset opacity and size back to normal, then reposition.
        self.ids.balloon_image.opacity = 1
        self.ids.balloon_image.size = (200, 200)
        self.reposition_balloon()

    
    def reposition_balloon(self):
        # self.current_position = random.choice(self.positions)
        previous_position = self.current_position
        possible_positions = [p for p in self.positions if p != previous_position] if previous_position else self.positions
        self.current_position = random.choice(possible_positions)
        print(f"Balloon position: {self.current_position}")

        # Randomly choose one of five balloon GIFs.
        gifs = [
            "Images/balloon_pop/balloon1.gif",
            "Images/balloon_pop/balloon2.gif",
            "Images/balloon_pop/balloon3.gif",
            "Images/balloon_pop/balloon4.gif",
            "Images/balloon_pop/balloon5.gif"
        ]
        chosen_gif = random.choice(gifs)
        self.ids.balloon_image.source = chosen_gif

        if self.current_position == 'Center':
            self.ids.balloon_image.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        elif self.current_position == 'Left':
            self.ids.balloon_image.pos_hint = {'center_x': 0.15, 'center_y': 0.5}
        elif self.current_position == 'Right':
            self.ids.balloon_image.pos_hint = {'center_x': 0.85, 'center_y': 0.5}
        elif self.current_position == 'Up':
            self.ids.balloon_image.pos_hint = {'center_x': 0.5, 'center_y': 0.85}
        elif self.current_position == 'Down':
            self.ids.balloon_image.pos_hint = {'center_x': 0.5, 'center_y': 0.15}
     
    def eye_navigation(self):
        if CameraWidget.direction:
            direction = CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None

    def on_key_down(self, window, key, keycode, codepoint, modifier):
        key_map = {273: "Up", 274: "Down", 275: "Right", 276: "Left", 32: "Space"}
        if key in key_map:
            self.navigate_action(key_map[key])

    def navigate_action(self, direction, dt = None):
        if self.manager.current == 'balloon' and not Notification.is_active:
            if direction == "Space":
                CameraWidget.game_mode = not CameraWidget.game_mode
            if CameraWidget.game_mode:
                print(f"CameraWidget.direction: {direction}, Current Position: {self.current_position}")
                if direction == self.current_position:
                    self.pop_balloon()
            else:
                if direction=="Up":
                    self.manager.current = 'option'

    def display_score_image(self):
        # Remove existing image if it exists
        if self.score_image:
            self.remove_widget(self.score_image)
        # Select the image based on the outcome
        img_source = "Images/HIGHEST_STREAK.gif"
        # Display win/lose image
        self.score_image = Image(source=img_source, size_hint=(1, 1),
                                pos_hint={'center_x': 0.4, 'center_y': 0.5}, opacity=1)
        self.add_widget(self.score_image)
        # Schedule fade-out after 2 seconds
        Clock.schedule_once(self.fade_out_score_image, 2)

    def fade_out_score_image(self, *args):
        if self.score_image:
            fade_out = Animation(opacity=0, duration=1)
            fade_out.bind(on_complete=lambda *x: self.remove_score_image())
            fade_out.start(self.score_image)

    def remove_score_image(self):
        if self.score_image:
            self.remove_widget(self.score_image)
            self.score_image = None