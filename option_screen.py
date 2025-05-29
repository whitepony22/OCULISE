from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.app import App
from camera_widget import CameraWidget, Notification
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, RoundedRectangle
from kivy.uix.button import Button

class OptionScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.selected_index = 0
        self.colors = [
            (0.243, 0.157, 0.325, 0.6),  # Color for button 1
            (0.333, 0.4, 0.725, 0.6),   # #5566b9
            (1, 0.9333, 0.8941, 0.6),  # Color for button 3
            (0.651, 0.682, 0.890, 0.6),  # #a6aee3
            (141/255, 102/255, 142/255, 0.6) # #8d668e
        ]

    def on_enter(self):
        # Collect all Button widgets inside the screen (including nested ones)
        self.buttons = {
        'IoT': self.ids.IoT,
        'news': self.ids.news,
        'balloonpop': self.ids.games.children[0].children[2],
        'raincatcher': self.ids.games.children[0].children[1],
        'wordgame': self.ids.games.children[0].children[0] }
        # Bind size and pos changes to auto-update the highlight
        for btn in self.buttons.values():
            btn.bind(size=self.update_highlight, pos=self.update_highlight)

        self.update_highlight()
        CameraWidget.camera_layout.pos_hint = {"top": 1, "right": 1}
        # Bind keyboard events.
        Window.bind(on_key_down=self.on_key_down)

    def on_leave(self):
        Window.unbind(on_key_down=self.on_key_down)
        # CameraWidget.direction=None

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
        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        if self.manager.current == 'option' and not Notification.is_active:
            if direction == "Left":
                self.move_selection(-1)
            elif direction == "Right":
                self.move_selection(1)
            elif direction == "Down":
                self.option_selected()
            elif direction == "Up":
                self.manager.current = 'home'

    def move_selection(self, direction):
        # Cycle through options
        self.selected_index = (self.selected_index + direction) % len(self.buttons)
        self.update_highlight()

    def update_highlight(self, *args):
        print(f"update_highlight called. Window size: {Window.size}")
        if not hasattr(self, 'buttons') or not self.buttons:
            print("Buttons not initialized or empty.")
            return
        for i, btn in enumerate(self.buttons.values()):
            # Clear only Color and RoundedRectangle instructions
            btn.canvas.before.remove_group('highlight')
            # Ensure size and position are settled before drawing
            print(f"Button size: {btn.size}, pos: {btn.pos}")
            with btn.canvas.before:
                Color(*self.colors[self.selected_index]) if i == self.selected_index else Color(0, 0, 0, 0)
                RoundedRectangle(size=btn.size, pos=btn.pos, radius=[20], group='highlight')

    def change_texture(self, new_texture_path):
        if hasattr(self.ids.IoT, 'bg_rect'):
            texture = CoreImage(new_texture_path).texture
            self.ids.IoT.bg_rect.texture = texture

    def option_selected(self):
        # Get the key of the currently selected button
        selected_key = list(self.buttons.keys())[self.selected_index]
        
        if selected_key == 'IoT':
            self.manager.current = 'iot'
        elif selected_key == 'balloonpop':
            self.manager.current = 'balloon'
        elif selected_key == 'raincatcher':
            self.manager.current = 'rain'
        elif selected_key == 'wordgame':
            self.manager.current = 'word'
        elif selected_key == 'news':
            self.manager.current = 'news'
        else:
            print("Unknown option:", selected_key)

    def update_gamemode_icon(self, instance, value):
        if value == False:
            CameraWidget.gamemode_icon.source = 'Images/DEFAULT.png'
        # else:
        #     if CameraWidget.game_mode:
        #         CameraWidget.gamemode_icon.source = 'Images/TYPE_ACTIVE.png'
        #     else:
        #         CameraWidget.gamemode_icon.source = 'Images/TYPE_INACTIVE.png'