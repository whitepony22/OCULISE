from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.core.window import Window
from kivy.clock import Clock
from camera_widget import CameraWidget, Notification
from kivy.properties import ListProperty
from kivy.core.window import Window

class HelpScreen(Screen):

    window_size = ListProperty(Window.size)

    def __init__(self, **kwargs):
        super(HelpScreen, self).__init__(**kwargs)
        # Clock.schedule_interval(self.check_direction_and_navigate, 5)

    def on_enter(self):
        # Bind the key down event when the screen is entered
        Window.bind(on_key_down=self.on_key_down)
        print(HelpScreen.window_size)
        CameraWidget.camera_layout.pos_hint = {"top": 1, "right": 1}
        #Clock.schedule_interval(self.check_direction_and_navigate, 5)

    def on_leave(self):
        # Unbind the key down event when leaving the screen
        Window.unbind(on_key_down=self.on_key_down)
        #Clock.unschedule(self.check_direction_and_navigate)

    def on_size(self, *args):
        self.window_size = [self.width, self.height]  # Update window_size on window resize
        print(self.window_size)

    def navigate_action(self, direction):
        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        print(f"Help screen navigation: {direction}")
        if self.manager.current == 'help' and not Notification.is_active:
            if direction == "Up":  # Navigate to 'type' screen
                self.manager.current = 'type'

    def eye_navigation(self):
        if CameraWidget.direction:
            direction=CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None  # Reset after processing

    def on_key_down(self, window, key, keycode, codepoint, modifier):
        key_map = {273: "Up", 276: "Left", 275: "Right"}
        if key in key_map:
            self.navigate_action(key_map[key])