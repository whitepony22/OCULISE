from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.uix.image import Image
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import ObjectProperty, NumericProperty, BooleanProperty
from speech import speak_phrase
from threading import Thread
from search_widget import SearchWidget
from chat_widget import ChatWidget
from file_widget import FileWidget
from list_widget import ListWidget
from camera_widget import CameraWidget, AlertPopup, Notification
from typing_widget import TypingWidget
from keyboard_widget import KeyboardWidget

class TypeScreen(Screen):
    list_widget = None  # Reference to the ListWidget
    search_widget = None  # Reference to the SearchWidget
    chat_widget = None 
    file_widget = None
    keyboard_widget = None
    typing_widget = ObjectProperty(None)  # Reference to the TextInput widget
    prediction_width = NumericProperty(0)  # Declare the property with a default value
    type_for_chat = BooleanProperty(False) # Check if the type mode is for chat
    file_for_chat = BooleanProperty(False) # Check if the file was opened for chat
    
    def __init__(self, **kwargs):
        super(TypeScreen, self).__init__(**kwargs)

        self.list_widget = ListWidget()  # Create an instance of ListWidget
        self.search_widget = SearchWidget()  # Create an instance of SearchWidget
        self.chat_widget = ChatWidget() # Create an instance of ChatWidget
        self.file_widget = FileWidget()
        self.keyboard_widget = KeyboardWidget()
        self.typing_widget = TypingWidget()# self.camera_widget = CameraWidget(sm = ScreenManager())
        
        self.add_widget(self.list_widget)  # Add ListWidget to the screen
        self.add_widget(self.search_widget)
        self.add_widget(self.chat_widget)
        self.add_widget(self.file_widget)  # Add SearchWidget to the screen
        self.add_widget(self.keyboard_widget)

        self.typing_widget = self.ids.typing_widget  # Added for separation of typing_widget
        self.ids.typing_widget.parent_screen = self

        self.hide_list_widget()  # Ensure it's hidden by default
        self.hide_search_widget()
        self.hide_file_widget()
        self.hide_chat_widget()
        self.hide_keyboard_widget()

        self.ids.typing_widget.bind(caps=self.on_caps)
        self.caps_icon = None

        # Bind the text change event
        self.ids.typing_widget.bind(text=self.adjust_heights)
        self.last_text = ""

        self.browser = None
        # Clock.schedule_interval(self.check_direction_and_navigate, 5)

        # Bind to the window resize event
        Window.bind(on_resize=self.on_window_resize)

    def on_type_for_chat(self, instance, value):
        print(f"Change in Type for chat: {value}")
        if value:
            print(f"Type for chat is True, type mode is active")
            # Delay the activation of type mode by 0.1 seconds
            Clock.schedule_once(self.activate_type_mode, 0.1)
        else:
            # Cancel the clock if type_for_chat becomes False
            if hasattr(self, 'chat_clock'):
                self.chat_clock.cancel()
                self.chat_clock = None

    def activate_type_mode(self, dt):
        CameraWidget.type_mode = True
        CameraWidget.typemode_icon.source = 'Images/TYPE_ACTIVE.png'
        if self.typing_widget.text == '↓':
            self.typing_widget.do_backspace()
        if (self.chat_widget.ids.message_label.text not in ["Down to type message","Right to get text here"] and 
                self.chat_widget.ids.message_label.text != ""):
            self.typing_widget.insert_text(self.chat_widget.ids.message_label.text)
        self.chat_clock = Clock.schedule_interval(self.check_type_mode, 0.1)
        print("Clock started to check for change in type mode")

    def check_type_mode(self, dt):
        # Check if type_mode has become False
        if not CameraWidget.type_mode:
            # Perform the desired action when type_mode becomes False
            self.chat_widget.opacity = 1
            self.chat_widget.disabled = False
            message = self.get_typing_widget_text().strip()
            if message:
                self.chat_widget.ids.message_label.text = message
            else:
                self.chat_widget.ids.message_label.text = "Down to type message"
            self.typing_widget.clear_text()
            self.type_for_chat = False  # Reset the flag

            # Unschedule the clock once the action has been performed
            print(f"Chat clock value: {self.chat_clock}")
            if self.chat_clock:
                self.chat_clock.cancel()
                self.chat_clock = None

    def on_window_resize(self, window, width, height):
        """Handle window resize event."""
        window_size = (width, height)
        print(f"Window resized to: {window_size}")
        # self.adjust_heights(self.ids.typing_widget, self.ids.typing_widget.text)
        minimized_size = (1000,750)
        maximized_size = (1920,1051)

    def show_list_widget(self):
        self.list_widget.show()  # Show the list widget
        
    def hide_list_widget(self):
        self.list_widget.hide()  # Hide the list widget
        # self.focus = True

    def show_file_widget(self):
        self.file_widget.opacity = 1  # Show the list widget
        self.file_widget.selected_index = -1
        self.file_widget.ids.save_button.source = "Images/SAVE_HIGHLIGHTED.png"
        self.file_widget.current_index = 0
        if self.file_for_chat:
            self.file_widget.ids.save_button.source = 'Images/SAVE_DEFAULT.png'
            self.file_widget.selected_index = 0
        self.file_widget.update_file_display()  # Highlight the first phrase
        CameraWidget.typemode_icon.source = 'Images/DEFAULT.png'

    def hide_file_widget(self):
        self.file_widget.opacity = 0 # Hide the list widget
        if self.file_for_chat:
            print("file widget hidden from chat widget")
            self.file_widget.row = 9
            self.file_for_chat = False
            self.chat_widget.ids.message_label.text = "Down to type message"
        if CameraWidget.typemode_icon:
            CameraWidget.typemode_icon.source = 'Images/TYPE_ACTIVE.png' if CameraWidget.type_mode else 'Images/TYPE_INACTIVE.png'        

    def show_search_widget(self):
        self.search_widget.show()
        
    def hide_search_widget(self):
        self.search_widget.hide()

    def show_chat_widget(self):
        self.chat_widget.show()

    def hide_chat_widget(self):
        self.chat_widget.hide()

    def show_keyboard_widget(self):
        self.keyboard_widget.show()

    def hide_keyboard_widget(self):
        self.keyboard_widget.hide()

    def on_enter(self):
        Window.bind(on_key_down=self.on_key_down)  # Bind keyboard events on entering screen
        CameraWidget.camera_layout.pos_hint = {"top": 1, "right": 1}
        CameraWidget.typemode_icon.source = 'Images/TYPE_INACTIVE.png'
        self.typing_widget.focus = True
        CameraWidget.type_mode = False
        # direction = None

    def on_leave(self):
        # self.camera_widget.ids.direction_label.color = (1, 1, 1, 1)
        CameraWidget.type_mode = False
        CameraWidget.typemode_icon.source = 'Images/DEFAULT.png'
        if not CameraWidget.type_mode:
            Window.unbind(on_key_down=self.on_key_down)  # Unbind keyboard events when leaving screen
        # else:
            self.typing_widget.unbind(on_key_down=self.typing_widget.keyboard_on_key_down)

    def navigate_action(self, direction, keycode = None):
        print(f"Type screen navigation: {direction}")
        print(f"[DEBUG] navigate_action called: {direction}, current screen: {self.manager.current}")
        print(f"[DEBUG] type_mode: {CameraWidget.type_mode}, current focus: {self.typing_widget.focus}")

        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        if self.manager.current == 'type' and not Notification.is_active:
            if CameraWidget.type_mode:
                self.typing_widget.focus = True
                print('ids in type:', self.ids)
                self.typing_widget.typing_navigate_action(direction)
                return
            # Actions for the type screen
            elif self.list_widget.opacity == 0 and self.search_widget.opacity == 0 and self.chat_widget.opacity == 0 and self.file_widget.opacity == 0:  # If ListWidget is hidden
                if direction == "Right":  # Right arrow key pressed
                    self.manager.current='home'
                    CameraWidget.direction= None
                elif direction == "Up":  # Up arrow key
                    self.ids.go_to_list.opacity = 0
                    self.ids.go_to_files.opacity = 0
                    self.ids.go_to_menu.opacity = 0
                    self.ids.go_to_help.opacity = 0
                    self.show_list_widget()  # Show ListWidget when pressing up arrow
                    CameraWidget.direction= None
                elif direction == "Left": # Left arrow key
                    self.show_file_widget()
                    print("file shown using arrow")
                    CameraWidget.direction= None
                elif direction == "Down":  # Down arrow key
                    self.manager.current="help"
                    # self.show_keyboard_widget()
                    CameraWidget.direction= None
            # When the ListWidget is in control
            elif self.list_widget.opacity == 1 or self.search_widget.opacity == 1 or self.chat_widget.opacity == 1:
                print("List widget is in control")
                self.list_widget.navigate_direction(direction, self)
            # When file widget is in control
            elif self.file_widget.opacity == 1:
                if direction == "Left":
                    if self.file_widget.selected_index == -1:  
                        self.save_typed_content()
                    else:
                        self.delete_content_and_update(self.file_widget.selected_index) 
                elif direction == "Down":
                    self.file_widget.move_selection_down()
                elif direction == "Up" or direction == "Left":
                    self.hide_file_widget()
                elif direction == "Right":
                    self.typing_widget.insert_text(self.file_widget.get_highlighted_text())
                    self.hide_file_widget()

    def eye_navigation(self):
        if CameraWidget.direction:
            print(f"[DEBUG] Eye navigation detected: {CameraWidget.direction}")
            direction = CameraWidget.direction
            self.navigate_action(direction)
            CameraWidget.direction = None

    def on_key_down(self, window, key, keycode, codepoint, modifier):
        if self.manager.current == 'type':
            key_map = {275: "Right", 273: "Up", 276: "Left", 274: "Down"}
            if key in key_map:
                print(f"[DEBUG] Key event: {key_map[key]} detected, passing to navigate_action()")
                print(f"Key: {key}, key_map: {key_map[key]}")
                self.navigate_action(key_map[key])

    def on_kv_post(self, base_widget):
        """Bind the typing_widget's prediction_width to dynamically update."""
        self.ids.typing_widget.bind(prediction_width=self.set_prediction_width)

    def save_typed_content(self):
        # Get the text from the typing widget
        normalized_text = self.get_typing_widget_text()
        print(f"Typed content: {normalized_text}")
        # Check if there is any content to save
        if not normalized_text.strip():  # Avoid saving empty or whitespace-only content
            print("No content to save.")
            AlertPopup(message = "No content to save.").open()
            self.hide_file_widget()
            return
        file_name = "C:/Program Files/Python312/Main Project/Interface/OCULISE/K_Kivy12.6 (Chat)/typed_content.txt"  # Name of the file to save content
        try:
            # Read the existing content of the file (if it exists)
            try:
                with open(file_name, "r") as file:
                    existing_content = file.read()  # Read the entire file as a string
            except FileNotFoundError:
                existing_content = ""  # File doesn't exist yet
            # Check if the normalized content already exists in the file
            if normalized_text in existing_content:
                print("Content already exists in the file. Not saving again.")
                AlertPopup(message = "Content already exists in the file. Not saving again.").open()
                self.hide_file_widget()
                return
            # Save the new content to the file
            with open(file_name, "a") as file:
                file.write(normalized_text + "\n---\n")  # Add extra spacing for clarity
            print(f"Content saved:\n{normalized_text}")
            AlertPopup(message = "Content saved.").open()
        except Exception as e:
            print(f"Error saving content: {e}")
            AlertPopup(message = f"Error saving content: {e}").open()
        self.hide_file_widget()

    def delete_content_and_update(self,index):
        for entry in self.file_widget.entries:
            if entry == self.file_widget.get_highlighted_text():
                self.file_widget.entries.remove(entry)
                break
        print("delete function")
        print(self.file_widget.entries)
        with open('C:/Program Files/Python312/Main Project/Interface/OCULISE/K_Kivy12.6 (Chat)/typed_content.txt', 'w') as file:
            for entry in self.file_widget.entries:
                file.write(entry + '\n---\n')
        self.file_widget.refresh_buttons()

    def set_prediction_width(self, instance, value):
        """Update the prediction_width dynamically based on typing_widget."""
        if value != 0:
            self.prediction_width = value + 10
        else:
            self.prediction_width = 0

    def on_caps(self, instance, value):
        """This method is triggered whenever 'caps' changes."""
        img_source = "Images/CAPS_ON.png" if value == 0 else "Images/CAPS_OFF.png"
        # Perform actions based on the new value of caps (0 or 1)
        self.display_caps_icon(img_source)

    def display_caps_icon(self, img_source):
        # Remove the existing image if it exists
        if self.caps_icon:
            self.remove_widget(self.caps_icon)
        # Select the image based on the mode
        self.caps_icon = Image(source=img_source, size_hint=(0.3, 0.3), pos_hint={'center_x': 0.5, 'center_y': 0.5}, opacity=1)
        self.add_widget(self.caps_icon)
        # Schedule the fade-out effect after 2 seconds
        Clock.schedule_once(self.fade_out_caps_icon, 2)

    def fade_out_caps_icon(self, *args):
        if self.caps_icon:
            # Create an animation to fade out the image
            fade_out = Animation(opacity=0, duration=1)
            fade_out.bind(on_complete=lambda *x: self.remove_caps_icon())  # Remove the widget after fading
            fade_out.start(self.caps_icon)

    def remove_caps_icon(self):
        if self.caps_icon:
            self.remove_widget(self.caps_icon)
            self.caps_icon = None

    def adjust_heights(self, instance, value):
        # Calculate new height for typing_widget based on content
        if value.count('\n') > self.last_text.count('\n'):
            num_lines = len(instance._lines) + 1  # Number of lines in the TextInput
            line_height = instance.line_height
            new_typing_height = min(500, max(100, num_lines * line_height))
            # Calculate new height for scrollview
            remaining_height = 200 - (new_typing_height - 100)
            new_scroll_height = max(100, remaining_height)
            # Update heights
            self.ids.typing_widget.height = new_typing_height
            self.ids.prediction_scroll.height = new_scroll_height
        self.last_text = value

    def get_typing_widget_text(self):
        #This function retrieves the text from the TextInput widget.
        user_input = self.typing_widget.text
        # Remove arrow characters
        for arrow in ['→', '←', '↑', '↓']:
            user_input = user_input.replace(arrow, '')
        return user_input
        
    def speak_user_input(self):
        """Retrieve the text from the TextInput and use the TTS function to speak it."""
        user_input = self.get_typing_widget_text()
        if user_input.strip():  # Ensure there is input to speak
            self.speaking_gif = Image(source='Images/SPEAKING.gif', anim_delay=0.1) # Add the GIF animation
            self.add_widget(self.speaking_gif)
            # speak_phrase(user_input)  # Use the TTS function to speak the input
            Thread(target=speak_phrase, args=(user_input,)).start() # Start TTS in a separate thread to prevent blocking
            Clock.schedule_once(lambda dt: self.remove_widget(self.speaking_gif), 3)  # Stop the animation after 3 seconds
        else:
            print("No input to speak.")  # Optionally handle the case where there's no input
            AlertPopup(message = "No input to speak.").open()

    def search(self):
        # Hide ListWidget and show SearchWidget when 'Search' is pressed
        self.hide_list_widget()
        self.show_search_widget()
        # Get the search query from the input widget
        search_query = self.get_typing_widget_text()
        if search_query:
            # Call on_search and pass the search query to it
            #SearchWidget.on_search(search_query)
            self.search_widget.on_search(search_query)
        else:
            AlertPopup(message = "No search query entered.").open()
            print("No search query entered.")

    def chat(self):
        """Show the ChatWidget when 'Chat' is pressed."""
        self.hide_list_widget()
        self.show_chat_widget()
        self.chat_widget.create_sender_buttons()
        self.chat_widget.clear_bubbles()
        CameraWidget.camera_layout.pos_hint = {"y": 0, "x": 0}

    def get_balloon_pop(self):
        self.manager.current = 'balloon'

    def get_rain_catcher(self):
        self.manager.current = 'rain'