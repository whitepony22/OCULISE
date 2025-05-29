from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.core.window import Window
from kivy.uix.image import Image
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
from camera_widget import CameraWidget, Notification
import iot_blynk_connect as B

class IoTScreen(Screen):
    def __init__(self, **kwargs):
        super(IoTScreen, self).__init__(**kwargs)

        self.fan_state = 'off'  # Track the current state of the fan
        self.light_state = 'off'  # Track the current state of the light

        # Create a layout for the buttons
        self.layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.5))

        # Create the fan image (initially hidden)
        self.fan_image = Image(source='Images/OFF.png', size_hint=(0.5, 0.80), pos_hint={'x': 0.25, 'y': 0.45})  # Takes half of the width
        self.layout.add_widget(self.fan_image)

        # Create the light image (initially hidden)
        self.light_image = Image(source='Images/OFF.png', size_hint=(0.5, 0.80), pos_hint={'x': 0.75, 'y': 0.45})  # Takes half of the width
        self.layout.add_widget(self.light_image)

        # Add the layout to the IoT screen
        self.add_widget(self.layout)

    def on_enter(self):
        self.fan_state = 'off'
        self.light_state = 'off'
        self.fan_image.source = 'Images/OFF.png'  # Ensure the fan image shows OFF
        self.light_image.source = 'Images/OFF.png'  # Ensure the light image shows OFF
        CameraWidget.camera_layout.pos_hint = {"y": 0, "right": 1}
        Window.bind(on_key_down=self.on_key_down)

    def on_leave(self):
        Window.unbind(on_key_down=self.on_key_down)

    def go_home(self):
        self.manager.current = 'home'

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
        print(f"iot Current direction: {direction}")
        if self.manager.current == 'iot' and not Notification.is_active:
            if direction == "Up":  # Up arrow key
                self.manager.current = 'option'
            elif direction == "Left":  # Left arrow key - toggle fan
                self.toggle_fan()
                if self.fan_image.source == 'Images/OFF.png':
                    B.set_fan_state(0)
                elif self.fan_image.source == 'Images/ON.png':
                    B.set_fan_state(1)
            elif direction == "Right":  # Right arrow key - toggle light
                self.toggle_light()
                if self.light_image.source == 'Images/OFF.png':
                    B.set_led_state(0)
                elif self.light_image.source == 'Images/ON.png':
                    B.set_led_state(1)

    # def select_device(self, device):
    #     self.ids.fan_button.background_color = 0.900, 0.600, 0.906, 1  # light purple
    #     self.ids.light_button.background_color = 0.6471, 0.3804, 0.8353, 1  # light violet
    #     if device == 'fan':
    #         self.ids.fan_button.background_color = 0.6627, 0.3255, 0.6784, 1  # Change FAN button color
    #         self.selected_device = 'fan'
    #         self.fan_image.opacity = 1  # Show fan image
    #         self.light_image.opacity = 1  # Hide light image
    #     elif device == 'light':
    #         self.ids.light_button.background_color = 0.5545, 0.3255, 0.6984, 1  # Change LIGHT button color
    #         self.selected_device = 'light'
    #         self.fan_image.opacity = 1  # Hide fan image
    #         self.light_image.opacity = 1  # Show light image

    def toggle_fan(self):
        self.fan_state = 'on' if self.fan_state == 'off' else 'off'
        self.fan_image.source = 'Images/ON.png' if self.fan_state == 'on' else 'Images/OFF.png'
        self.fan_image.reload()  # Reload the image to reflect the change

    def toggle_light(self):
        self.light_state = 'on' if self.light_state == 'off' else 'off'
        self.light_image.source = 'Images/ON.png' if self.light_state == 'on' else 'Images/OFF.png'
        self.light_image.reload()  # Reload the image to reflect the change