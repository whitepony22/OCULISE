from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.image import Image, AsyncImage
from kivy.animation import Animation
from kivy.core.window import Window
import cv2
from kivy.properties import BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color
from kivy.input.motionevent import MotionEvent
import eye_direction as EyeDir
from kivy.uix.popup import Popup
import key

class CameraWidget(FloatLayout):

    direction = None
    type_mode = BooleanProperty(True)  # Observable property for type mode
    camera_active = BooleanProperty(False)  # Camera starts inactive
    camera_layout = None
    typemode_icon = None
    gamemode_icon = None
    game_mode = False  # Game mode starts inactive
    transition_map = {
        'Left': 'right',
        'Right': 'left',
        'Up': 'down',
        'Down': 'up'
    }

    def __init__(self, sm, **kwargs):
        super().__init__(**kwargs)

        self.img_widget = self.ids.camera_feed  # Get image from KV
        self.label = self.ids.direction_label  # Get the label from KV
        self.countdown_label = self.ids.countdown_label  # Get the countdown label from KV

        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            self.label.text = "Camera not accessible"
            return

        self.countdown_active = False  # Countdown starts inactive
        self.current_frame = None

        self.sm = sm

        self.mode_image = None  # Placeholder for the image widget

        # Schedule events. Here we store the event so we can reschedule it later for game mode.
        Clock.schedule_interval(self.capture_frame, 1)  # Default update rate (1 FPS)
        Clock.schedule_interval(self.update_blink, 1)  # Blink detection every 1 second
        
        CameraWidget.typemode_icon = self.ids.typemode_icon
        CameraWidget.gamemode_icon = self.ids.gamemode_icon
        CameraWidget.camera_layout = self.ids.camera_layout
        
        self.sm.bind(current=self.on_screen_change)  # Bind to screen change
        self.bind(on_touch_down=self.on_touch_down)  # Bind mouse touch events
        # Use fbind to silently listen for key events without interfering with other bindings
        Window.fbind('on_key_down', self.on_key_down)

    def on_touch_down(self, touch, *args):
        """
        Handles mouse click events to activate or deactivate the camera.
        """
        if self.img_widget.collide_point(*touch.pos):  # Check if click is inside the widget
            print(f"Mouse click detected at {touch.pos}")
            self.toggle_camera_activation()
            return True
        elif self.ids.typemode_icon.collide_point(*touch.pos):  # Right half for type mode toggle
            print("Toggling type mode.")
            self.toggle_type_mode()
            return True
        elif self.ids.gamemode_icon.collide_point(*touch.pos):  # Right half for type mode toggle
            print("Toggling type mode.")
            self.toggle_game_mode()
            return True
        self.img_widget.focus = False
        Window.release_all_keyboards()
        print(touch.pos)
        # Ensure touch is a valid MotionEvent before passing it to super()
        if isinstance(touch, MotionEvent):
            return super().on_touch_down(touch)
        else:
            print(f"Invalid touch event: {touch}")
            # CameraWidget.game_mode = False
            return False
        # return super().on_touch_down(touch) # Pass the event to the parent class for further processing

    def on_key_down(self, window, key, *args):
        print(f'listened to key {key} from camera_widget')
        if key == 275 and self.sm.current == 'word' and self.ids.games_home.opacity == 1:  # Right arrow key
            print('Key request to toggle game mode from camera_widget')
            self.toggle_game_mode()

    def on_screen_change(self, *args):
        if self.sm.current not in ['balloon', 'word']:
            if self.ids.games_home:
                self.ids.games_home.opacity = 0

    def start_countdown(self, seconds=3):
        if not self.camera_active:  # Start countdown only if the camera is active
            return

        self.countdown = seconds
        self.countdown_active = True
        self.update_countdown_display()  # Display initial countdown value
        Clock.schedule_interval(self.decrement_countdown, 1)  # Schedule countdown every second

    def update_countdown_display(self):
        self.countdown_label.text = f"{self.countdown}"

    def decrement_countdown(self, dt):
        if self.countdown > 1:
            self.countdown -= 1
            self.update_countdown_display()
        else:
            self.countdown_label.text = " "
            self.update_eye_direction()  # Capture the frame after countdown
            Clock.unschedule(self.decrement_countdown)  # Stop the countdown
            self.countdown_active = False  # Countdown is no longer active

    def capture_frame(self, dt=None):
        ret, frame = self.capture.read()
        if not ret:
            return

        frame = cv2.flip(frame, 0)
        self.current_frame = frame

        if self.camera_active:
            if CameraWidget.game_mode:
                # In game mode, update eye direction on every frame (real-time)
                self.update_eye_direction()
            elif not self.countdown_active:
                self.start_countdown(3)

    def update_blink(self, dt=None):
        if self.current_frame is None:
            return 

        # Call blink detection function
        blink_status = EyeDir.detect_blink(self.current_frame, self.update_label)
        if blink_status == "Long Blink":
            self.toggle_camera_activation()
        elif blink_status == "Short Blink":
            # Toggle type mode on type screen, or game mode on game screen.
            if self.sm.current == "type":
                self.toggle_type_mode()
            elif self.sm.current in ['balloon', 'rain', 'word']:
                self.toggle_game_mode()

    def update_eye_direction(self, dt=None):
        # Skip further processing if the camera is inactive
        if not self.camera_active or self.current_frame is None:
            return
        frame = self.current_frame

        # Display the current frame in the image widget
        buf = frame.flatten()
        buf = buf = cv2.flip(frame, 1).tobytes()  # Flip horizontally for correct display
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_widget.texture = image_texture

        # Get eye direction and update the label
        direction = EyeDir.detect_eye_direction(frame)
        if direction is not None:
            CameraWidget.direction = direction
            self.label.text = f"Direction: {direction}"
            
            current_screen = self.sm.current
            if current_screen in ['home', 'type', 'help', 'option', 'iot', 'balloon', 'rain', 'word', 'news']:
                self.sm.get_screen(current_screen).eye_navigation()
        
        print('Game mode!!: ', CameraWidget.game_mode)

        # In non-game mode, Schedule a pause for 2 seconds before starting the next countdown
        if not CameraWidget.game_mode and not self.countdown_active:  # Start countdown only if not already active
            Clock.schedule_once(self.reset_frame_ready, 2)
        # else:
        #     # Optionally, in game mode you might clear or update the countdown label differently.
        #     self.countdown_label.text = ""

    def toggle_camera_activation(self):
        self.camera_active = not self.camera_active
        self.label.text = "CAM: ACTIVE" if self.camera_active else " "
        
        if self.camera_active:
            fallback_image = CoreImage("Images/DEFAULT.png").texture
            self.img_widget.texture = fallback_image  # Display the transparent fallback image
            self.start_countdown(3)  # Start countdown if the camera becomes active
        else:
            Clock.unschedule(self.decrement_countdown)  # Stop countdown if camera is deactivated
            self.countdown_label.text = ""  # Clear the countdown label
            CameraWidget.direction='Unknown'
            fallback_image = CoreImage("Images/CAM_INACTIVE.png").texture
            self.img_widget.texture = fallback_image  # Display the transparent fallback image

    def toggle_type_mode(self):
        if self.sm.current == 'type':
            if (self.sm.get_screen('type').file_widget.opacity == 1 or
                self.sm.get_screen('type').list_widget.opacity == 1 or
                self.sm.get_screen('type').search_widget.opacity == 1 or
                self.sm.get_screen('type').chat_widget.opacity == 1):
                print("Some widget is visible on type_screen. Type mode cannot be toggled.")
                return
            CameraWidget.type_mode = not CameraWidget.type_mode
            self.display_mode_image(mode = 'type')
            if CameraWidget.type_mode:
                self.ids.typemode_icon.source = 'Images/TYPE_ACTIVE.png'
            else:
                self.ids.typemode_icon.source = 'Images/TYPE_INACTIVE.png'

    def toggle_game_mode(self):
        # This method toggles game mode only when on the game screen.
        if self.sm.current not in ['balloon','rain','word']:
            return
        CameraWidget.game_mode = not CameraWidget.game_mode
        self.display_mode_image(mode = 'game')
        # Update gamemode icon
        self.ids.gamemode_icon.source = 'Images/GAME_ACTIVE.png' if CameraWidget.game_mode else 'Images/GAME_INACTIVE.png'
        # Update the game home
        self.update_game_home()

    def update_game_home(self):
        print(self.ids.games_home.canvas.before.children)
        # Set background color based on screen
        if self.sm.current in ['balloon']:
            # self.ids.games_home.canvas.before.children[1].rgba = (1, 0.9333, 0.8941, 0.8)  #ffeee4 background color
            for instr in self.ids.games_home.canvas.before.children:
                if isinstance(instr, Color):
                    instr.rgba = (0.9, 0.8333, 0.7941, 0.8)  #ffeee4 background color
                    break
            self.ids.skip.opacity = 0 # Show skip only in word mode

        elif self.sm.current in ['rain']:
            # self.ids.games_home.canvas.before.children[1].rgba = (1, 0.9333, 0.8941, 0.8)  #ffeee4 background color
            for instr in self.ids.games_home.canvas.before.children:
                if isinstance(instr, Color):
                    instr.rgba = (0.606, 0.680, 0.688, 0.6)  #ffeee4 background color
                    break
            self.ids.skip.opacity = 0 # Show skip only in word mode

        elif self.sm.current == 'word':
            # Find the Color instruction dynamically
            for instr in self.ids.games_home.canvas.before.children:
                if isinstance(instr, Color):
                    instr.rgba = (141/255, 102/255, 142/255, 0.8)  #8d668e
                    break
            self.ids.skip.opacity = 1 # Show skip only in word mode
        # Show games_home when game mode is inactive
        self.ids.games_home.opacity = 0 if CameraWidget.game_mode else 1

    def reset_frame_ready(self, dt):
        if self.camera_active:
            self.current_frame = None
            self.countdown_label.text = ""
            self.start_countdown(3)

    def update_label(self, message):
        """Update the direction label text."""

        # In game mode, ignore blink messages to preserve the direction label.
        if self.sm.current == 'balloon':
            return

        if message.isdigit() and self.sm.current == 'type':
            self.label.text = f'Blinked {message} sec'
        elif message.isdigit():
            if int(message) > 2:
                self.label.text = f'Blinked {message} sec'
        elif message == 'Face Detected':
            if not self.camera_active:
                self.label.text = message
            else:
                self.label.text = ''  # Clear the label when active
        elif self.camera_active:
            self.label.text = message
            CameraWidget.direction = "Unknown"  # Set direction to unknown
        # else:
        #     self.label.text = ''

    def display_mode_image(self, mode):
        # Remove the existing image if it exists
        if self.mode_image:
            self.remove_widget(self.mode_image)

        # Select the image based on the mode
        if mode == 'type':
            img_source = "Images/TYPE_MODE_ON.png" if CameraWidget.type_mode else "Images/TYPE_MODE_OFF.png"
        elif mode == 'game':
            img_source = "Images/GAME_MODE_ON.png" if CameraWidget.game_mode else "Images/GAME_MODE_OFF.png"

        self.mode_image = Image(source=img_source, size_hint=(0.4, 0.4), pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=1)
        self.add_widget(self.mode_image)

        # Schedule the fade-out effect after 2 seconds
        Clock.schedule_once(self.fade_out_mode_image, 2)

    def fade_out_mode_image(self, *args):
        if self.mode_image:
            # Create an animation to fade out the image
            fade_out = Animation(opacity=0, duration=1)
            fade_out.bind(on_complete=lambda *x: self.remove_mode_image())  # Remove the widget after fading
            fade_out.start(self.mode_image)

    def remove_mode_image(self):
        if self.mode_image:
            self.remove_widget(self.mode_image)
            self.mode_image = None

    def on_stop(self):
        if self.capture.isOpened():
            self.capture.release()

class AlertPopup(Popup):
    message = StringProperty('Error')

    def __init__(self, message, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        # Automatically dismiss the popup after 2 seconds
        Clock.schedule_once(self.dismiss, 2)

class Notification(FloatLayout):
    is_active = False  # Define is_active property
    auto_dismiss = BooleanProperty(True)  # Define auto_dismiss property
    message_text = StringProperty("")
    sender_name = StringProperty("")
    message_id = StringProperty("")
    profile_pic = StringProperty("")
    
    def __init__(self, message_text, chat_id, message_id, action_callback=None, profile_pic="", **kwargs):
        super().__init__(**kwargs)
        self.message_text = message_text
        self.chat_id = str(chat_id)
        self.sender_name = next((sender for sender, cid in key.chat_id.items() if str(cid) == str(chat_id)), "Unknown")
        self.message_id = str(message_id)
        self.profile_pic = profile_pic
        Notification.is_active = True  # Set notification to active
        print(f"Notification.is_active is on: {Notification.is_active}, chat_id: {self.chat_id}, profile_pic: {self.profile_pic}")
        self.action_callback = action_callback  # store the callback
        # Fade-in animation
        self.opacity = 0
        Animation(opacity=1, duration=0.5).start(self)
        # Request keyboard so we can capture arrow key events
        self.keyboard = Window.request_keyboard(self._key_closed, self)
        if self.keyboard:
            self.keyboard.bind(on_key_down=self._on_key_down)
        # If auto_dismiss is True, schedule dismissal after 3 seconds
        self.dismiss_event = Clock.schedule_once(lambda dt: self.dismiss(), 10) if self.auto_dismiss else None

    def _key_closed(self):
        if self.keyboard:
            self.keyboard.unbind(on_key_down=self._on_key_down)
            self.keyboard.release()
            self.keyboard = None

    def _on_key_down(self, keyboard, keycode, text, modifiers):
        # Determine which key was pressed and dismiss accordingly
        if keycode[1] == 'left':
            self.dismiss('left')  # dismiss fast
        elif keycode[1] == 'right':
            self.dismiss('right')
        self._key_closed()
        return True  # consume the event

    def dismiss(self, triggered_by=None, *args):
        Notification.is_active = False
        print(f"Notification.is_active is off: {Notification.is_active}")
        # If no trigger is provided, assume auto-dismiss
        if triggered_by is None:
            triggered_by = 'auto'
        # Call the callback if provided
        if self.action_callback:
            self.action_callback(triggered_by)
        # Cancel any scheduled auto-dismiss
        if self.dismiss_event is not None:
            Clock.unschedule(self.dismiss_event)
            self.dismiss_event = None
        # Fade-out animation and remove widget from parent
        parent = self.parent
        anim = Animation(opacity=0, duration=0.2)
        anim.bind(on_complete=lambda a, w, parent=parent: parent.remove_widget(self) if parent else None)
        anim.start(self)

"""    size_hint: 1, 0.4
    pos_hint: {'right': 1.6, 'y': -1.5}
    FloatLayout:
        pos: root.pos
        size: root.size
        Image:
            source: 'Images/NOTIFICATION.png'
            pos: root.pos
            size: root.size
        RelativeLayout:
            size_hint: 0.4, 0.5
            pos_hint: {'x': 0.4, 'top': 1}
            Label:
                id: message_text
                text: root.message_text
                font_size: 15
                text_size: self.size
                halign: "left"
                valign: "top"
                line_spacing: 0.2  # Decrease the spacing between lines
                color: 0, 0, 0, 1  # Black
                size_hint: 1, 1
                pos_hint: {'x': 0, 'top': 0.2}
            Label:
                id: notification_sender_name
                text: root.sender_name
                font_size: 20
                color: 0, 0, 0, 1  # Black
                size_hint: None, None
                size: self.texture_size
                pos_hint: {'x': 0, 'top': 0.8}
        Image:
            source: 'Images/circular.png'
            size_hint: 0.3, 0.9
            pos_hint: {'x': 0.2, 'top': 0.95}  # adjust as needed
            allow_stretch: True
            keep_ratio: True
            canvas.before:
                StencilPush
                Ellipse:
                    pos: self.pos
                    size: self.size
                StencilUse
            canvas.after:
                StencilUnUse
                StencilPop
"""