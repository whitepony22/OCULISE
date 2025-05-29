from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.core.window import Window
from speech import speak_phrase  # Import the speak_phrase function
from kivy.animation import Animation
from kivy.uix.button import Button
from kivy.clock import Clock
from camera_widget import CameraWidget, Notification
from emergency_widget import EmergencyWidget
from kivy.core.audio import SoundLoader
import iot_blynk_connect as B

# Message to send on emergency
msg = "Emergency!"

class HomeScreen(Screen):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set the initial size hints for the BoxLayouts
        self.left_box_size_hint = 0.2
        self.right_box_size_hint = 0.8
        # Add the emergency widget to the screen
        self.emergency_widget = EmergencyWidget()
        self.add_widget(self.emergency_widget)  # Add the emergency widget to the main screen
        # Load the emergency sound (adjust the path as needed)
        self.emergency_sound = SoundLoader.load('C:/Program Files/Python312/Main Project/Interface/OCULISE/bleep.mp3')

    def on_enter(self):
        # Bind the left and right arrow keys to switch between screens
        Window.bind(on_key_down=self.on_key_down)
        def position_camera(dt = 0):
            CameraWidget.camera_layout.pos_hint = {"top": 1, "x": 0}
        Clock.schedule_once(position_camera, 0.01)
        # Calculate total phrases dynamically based on grid layout's children
        grid_layout = self.ids.grid_layout
        buttons = sorted(grid_layout.children, key=lambda x: x.y)  # Sort by y position
        total_phrases = len(buttons)  # Get total number of buttons
        # Binding of button size to window change
        button = grid_layout.children[0]
        if button:
            button.bind(size=self.highlight_current_phrase, pos=self.highlight_current_phrase)
        if self.left_box_size_hint == 0.2:
            self.ids.grid_layout.opacity = 1
            self.ids.basic_phrase.opacity = 0
            self.ids.left_text.text = ' '
            self.ids.home_icon.source = 'Images/MENU_ICON.png'
            if total_phrases > 0:
                # self.current_phrase_index = 0
                self.current_phrase_index = total_phrases - 1
                self.highlight_current_phrase(skip_scroll=True)
            self.hide_emergency_widget()
            self.hide_home_button()
        else:
            self.ids.grid_layout.opacity = 0
            self.ids.basic_phrase.opacity = 1
            self.ids.left_text.text = 'TYPE\nNEW'
            self.ids.home_icon.source = 'Images/TYPE.png'
            self.show_home_button()
        self.update_box_layouts()

    def on_leave(self):
        # Unbind the keyboard events when leaving the screen
        Window.unbind(on_key_down=self.on_key_down)

    def speak_phrase(self, phrase):
        # Call the imported speak_phrase function
        speak_phrase(phrase)  # Replace this with your TTS function

    def go_home(self):
        # Navigate back to home screen
        self.manager.current = 'home'

    def show_emergency_widget(self):
        self.emergency_widget.show()  # Show the emergency widget
        self.is_emergency_visible = True
        CameraWidget.camera_layout.pos_hint = {"y": 0, "x": 0}

    def hide_emergency_widget(self):
        self.emergency_widget.hide()  # Hide the emergency widget
        self.is_emergency_visible = False
        if CameraWidget.camera_layout:
            CameraWidget.camera_layout.pos_hint = {"top": 1, "x": 0}

    def type_new_page(self):
        # Example of navigating to another page for typing
        pass

    def hide_home_button(self):
        # Hide the home button initially
        home_button = self.ids.home_button  # Replace with your actual home button id
        home_button.opacity = 0  # Hide the button

    def show_home_button(self):
        # Show the home button
        home_button = self.ids.home_button  # Replace with your actual home button id
        home_button.opacity = 1  # Show the button

    def navigate_phrases(self, direction):
        # Get total number of phrases dynamically based on grid layout's children
        grid_layout = self.ids.grid_layout
        buttons = sorted(grid_layout.children, key=lambda x: x.y)
        total_phrases = len(buttons)
        # Update the current phrase index within the valid range
        self.current_phrase_index = (self.current_phrase_index + direction) % total_phrases
        # Highlight the new current phrase
        self.highlight_current_phrase()

    def highlight_current_phrase(self, *args, skip_scroll=False):
        # Clear previous highlights
        buttons = sorted(self.ids.grid_layout.children, key=lambda x: x.y)  # Sort by y position
        buttons = [button for button in buttons if hasattr(button, 'text')]  # Ensure we only get buttons
        # Get the current window size
        window_size = Window.size
        # Check if the window is in full-screen mode
        is_full_screen = (window_size[0] >= 1500 and window_size[1] >= 800)
        # Determine the highlighted image based on full screen
        highlight_image = 'Images/HIGHLIGHTED_PHRASE.png' if is_full_screen else 'Images/HIGHLIGHTED_PHRASE_SMALL.png'
        for i, button in enumerate(buttons):
            # Reset all buttons to their original background image based on their index (odd/even)
            button.background_normal = 'Images/PHRASE.png' if i % 2 == 0 else 'Images/PHRASE_ALT.png'
        # Highlight the current phrase by changing its background image
        if 0 <= self.current_phrase_index < len(buttons) and self.left_box_size_hint == 0.2:
            button = buttons[self.current_phrase_index]
            button.background_normal = highlight_image  # Change to the highlighted image
            # Scroll to the highlighted phrase
            if not skip_scroll:
                self.scroll_to_element(button)

    def clear_highlights(self):
        # Clear any highlighted buttons
        buttons = sorted(self.ids.grid_layout.children, key=lambda x: x.y)  # Sort by y position
        buttons = [button for button in buttons if hasattr(button, 'text')]
        for i, button in enumerate(buttons):
            # Reset all buttons to their original background image based on their index (odd/even)
            button.background_normal = 'Images/PHRASE.png' if i % 2 == 0 else 'Images/PHRASE_ALT.png'

    def update_box_layouts(self):
        # Update size hints for both BoxLayouts based on current state
        left_box = self.ids.left_box  # Assuming you have ids for your BoxLayouts in the KV file
        right_box = self.ids.right_box
        left_box.size_hint_x = self.left_box_size_hint
        right_box.size_hint_x = self.right_box_size_hint

    def navigate_action(self, direction):
        print(f"Keyboard direction: {direction}")
        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        if self.manager.current == 'home' and not Notification.is_active:
            if direction == "Up":
                if self.left_box_size_hint == 0.5 and self.emergency_widget.opacity == 0:
                    self.show_emergency_widget()
                else:
                    self.navigate_phrases(1)
            elif direction == "Left":
                if self.emergency_widget.opacity == 1:
                    self.hide_emergency_widget()
                    if self.emergency_sound and self.emergency_sound.state == 'play':
                        self.emergency_sound.stop()
                elif self.left_box_size_hint == 0.5:
                    # Window.unbind(on_key_down=self.on_key_down)
                    self.manager.current = 'type'
                    CameraWidget.direction = None
                else:
                    # Return to default layout
                    self.left_box_size_hint = 0.5
                    self.right_box_size_hint = 0.5
                    self.current_phrase_index = len(self.ids.grid_layout.children) - 1
                    self.highlight_current_phrase()
                    self.update_box_layouts()
                    self.show_home_button()
                    self.ids.grid_layout.opacity = 0
                    self.ids.basic_phrase.opacity = 1
                    self.ids.left_text.text = 'TYPE\nNEW'
                    self.ids.home_icon.source = 'Images/TYPE.png'
            elif direction == "Right":
                if self.emergency_widget.opacity == 1:
                    if self.emergency_sound and self.emergency_sound.state != 'play':
                        self.emergency_sound.play()
                        B.message(msg)  # Send emergency message
                elif self.left_box_size_hint == 0.5:
                    # Expand to show phrases
                    self.left_box_size_hint = 0.2
                    self.right_box_size_hint = 0.8
                    self.current_phrase_index = len(self.ids.grid_layout.children) - 1
                    self.highlight_current_phrase()
                    self.update_box_layouts()
                    self.hide_home_button()
                    self.ids.grid_layout.opacity = 1
                    self.ids.basic_phrase.opacity = 0
                    self.ids.left_text.text = ' '
                    self.ids.home_icon.source = 'Images/MENU_ICON.png'
                    self.scroll_to_element(self.ids.grid_layout.children[-1])
                else:
                    self.speak_current_phrase()
            elif direction == "Down":
                if self.emergency_widget.opacity == 1:
                    self.hide_emergency_widget()
                    if self.emergency_sound and self.emergency_sound.state == 'play':
                        self.emergency_sound.stop()
                elif self.left_box_size_hint == 0.5:
                    # self.manager.current = 'iot'
                    self.manager.current = 'option'
                else:
                    self.navigate_phrases(-1)
            CameraWidget.direction=None

    def eye_navigation(self):
        if CameraWidget.direction:
            direction = CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None

    def on_key_down(self, window, key, keycode, codepoint, modifier):
        key_map = {273: "Up", 274: "Down", 275: "Right", 276: "Left", 32: "Space"}
        if key in key_map:
            self.navigate_action(key_map[key])

    def speak_current_phrase(self):
        # Speak the currently highlighted phrase
        buttons = sorted(self.ids.grid_layout.children, key=lambda x: x.y)  # Sort by y position
        buttons = [button for button in buttons if hasattr(button, 'text')]  # Ensure we only get buttons
        if 0 <= self.current_phrase_index < len(buttons):
            button = buttons[self.current_phrase_index]
            self.speak_phrase(button.text)  # Speak the highlighted phrase

    def scroll_to_element(self, widget):
        # Get the scroll view and grid layout
        scroll_view = self.ids.scroll_view
        grid_layout = self.ids.grid_layout
        # Calculate the widget's position in the grid
        widget_y = widget.y  # Y position of the widget in the grid
        widget_height = widget.height  # Height of the widget
        scroll_view_height = scroll_view.height  # Height of the ScrollView
        total_grid_height = grid_layout.height
        # Calculate the absolute top and bottom of the visible area in grid coordinates
        offset = widget_height
        visible_bottom = scroll_view.scroll_y * total_grid_height
        visible_top = visible_bottom + scroll_view_height
        # If the widget is above the visible area (but we want a slight nudge)
        if widget_y < visible_bottom + offset:
            # Scroll so the widget is offset pixels below the visible bottom
            target_y = max(widget_y - offset, 0)
        # If the widget is below the visible area (and we want a slight nudge)
        elif widget_y + widget_height > visible_top - offset:
            # Scroll so the bottom of the widget plus a margin is in view
            target_y = min(widget_y + widget_height + offset - scroll_view_height, total_grid_height - scroll_view_height)
        else:
            # The widget is already within a “nudge” range; no need to scroll.
            for child in grid_layout.children:
                if child.y + child.height > visible_bottom and child.y < visible_top:
                    # Ensure this button moves to the top
                    target_y = max(child.y - offset, 0)
                    break
            else:
                return  # No need to scroll
        # Clamp target_scroll_y between 0 and 1 and animate
        target_scroll_y = target_y / (total_grid_height - scroll_view_height)
        target_scroll_y = min(max(0, target_scroll_y), 1)
        animation = Animation(scroll_y=target_scroll_y, duration=0.3)
        animation.start(scroll_view)

    def get_basic_phrases(self):
        # Get the grid layout widget by its ID
        grid_layout = self.root.ids.grid_layout
        # List to store the button texts
        phrases = []
        # Loop through all the children of the grid_layout
        for child in grid_layout.children:
            # Check if the child is a Button
            if isinstance(child, Button):
                # Add the button text to the list
                phrases.append(child.text)
        return phrases