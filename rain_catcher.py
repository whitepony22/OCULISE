from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.audio import SoundLoader
from kivy.animation import Animation
from kivy.properties import NumericProperty
from kivy.storage.jsonstore import JsonStore
from camera_widget import CameraWidget, Notification
import random

class Raindrop(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'Images/raindrop.png'  # Add a raindrop image to your assets
        self.size_hint = (None, None)
        self.size = (50, 50)
        self.pos = (random.randint(0, int(0.75*Window.width - self.width)), Window.height)

    def fall(self, dt):
        self.y -= 5  # Speed of falling
        if self.y < 0 and self.parent:
            self.parent.remove_widget(self)  # Remove if missed

class RainGame(Screen):
    x_pos = NumericProperty(0)  # Bindable property
    score = NumericProperty(0)
    high_score = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sound = SoundLoader.load('water_drop.mp3')  # Add a sound effect file
        self.score_image = None
        # self.bucket = self.ids.get("bucket")
        self.bucket = self.ids.bucket
        self.x_pos = self.bucket.x  # Ensure x_pos starts correctly
        self.new_high_score_displayed = False

    def on_enter(self, *args):
        self.score = 0  # Reset score when starting
        self.new_high_score_displayed = False
        Clock.schedule_interval(self.spawn_raindrop, 1.5)
        Clock.schedule_interval(self.update, 1/50)
        Window.bind(on_key_down=self.on_key_down)
        CameraWidget.game_mode = True
        # Load high score from storage
        self.store = JsonStore('highscore.json')
        self.high_score = self.store.get('rain')['high'] if self.store.exists('rain') else 0
        CameraWidget.camera_layout.pos_hint = {"y": 0, "right": 1} 
        CameraWidget.gamemode_icon.source = 'Images/GAME_ACTIVE.png'

    def on_leave(self, *args):
        Clock.unschedule(self.update)
        Window.unbind(on_key_down=self.on_key_down)
        print("Key binding removed")  # Debugging statement
        CameraWidget.game_mode = False
        CameraWidget.gamemode_icon.source = 'Images/DEFAULT.png'

    def spawn_raindrop(self, dt):
        drop = Raindrop()
        self.add_widget(drop)
        Clock.schedule_interval(drop.fall, 1/50)

    def update(self, dt):
        if not hasattr(self.ids, "bucket"):
            print("Bucket ID missing!")  # Debugging statement
            return
        bucket = self.ids.bucket
        for drop in self.children[:]:
            if isinstance(drop, Raindrop) and drop.collide_widget(bucket):
                print("Collision detected!")
                if self.sound:
                    self.sound.play()
                self.catch_raindrop(drop)

    def catch_raindrop(self, drop):
        self.remove_widget(drop)  # Remove first to prevent multiple counts
        self.score += 1  # Increase score on catch
        if self.score > self.high_score:
            self.high_score = self.score
            self.store.put('rain', high=self.high_score)  # Save new high score
            if not self.new_high_score_displayed:
                self.display_score_image()
                self.new_high_score_displayed = True
        
    def eye_navigation(self):
        if CameraWidget.direction:
            direction = CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None

    def on_key_down(self, window, key, keycode, codepoint, modifier):
        key_map = {273: "Up", 274: "Down", 275: "Right", 276: "Left"}
        if key in key_map:
            self.navigate_action(key_map[key])

    def navigate_action(self, direction, dt=None):
        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        if self.manager.current == 'rain' and not Notification.is_active:
            if self.bucket:
                if CameraWidget.game_mode:
                    if direction == "Left":
                        self.move_left()
                    elif direction == "Right":
                        self.move_right()
                else:
                    if direction == "Up":
                        self.manager.current = 'option'
            else:
                print("Bucket ID not found in self.ids:", self.ids.keys())
            
    def move_left(self):
        if self.bucket.x > 0:
            new_x = max(self.bucket.x - 100, 0)
            Animation(x=new_x, duration=0.2).start(self.bucket)  # Smooth movement

    def move_right(self):
        if self.bucket.right < 0.75*Window.width:
            new_x = min(self.bucket.x + 100, 0.75*Window.width - self.bucket.width)
            Animation(x=new_x, duration=0.2).start(self.bucket)  # Smooth movement

    def display_score_image(self):
        # Remove existing image if it exists
        if self.score_image:
            self.remove_widget(self.score_image)
        # Select the image based on the outcome
        img_source = "Images/RAIN_NEW.gif"
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