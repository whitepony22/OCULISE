from kivy.uix.floatlayout import FloatLayout
from kivy.clock import Clock
from camera_widget import CameraWidget, AlertPopup
from chat_widget import ChatBubble
import time

class ListWidget(FloatLayout):
    
    def __init__(self, **kwargs):
        super(ListWidget, self).__init__(**kwargs)
        self.orientation = 'horizontal'
        self.opacity = 0  # Start hidden
        self.disabled = True  # Start disabled
        self.bind(disabled=self.update_typemode_icon)  # Update the type mode icon when visible

        self.chat_bubble = ChatBubble()

    def show(self):
        self.opacity = 1  # Make visible
        self.disabled = False  # Enable the widget
        CameraWidget.camera_layout.pos_hint = {"top": 1, "right": 1}
        
    def hide(self):
        self.opacity = 0  # Make hidden
        self.disabled = True  # Disable the widget
        
    def update_typemode_icon(self, instance, value):
        if value == False:
            # print("List in control: Hiding type mode icon.")
            CameraWidget.typemode_icon.source = 'Images/DEFAULT.png'
        else:
            # print("List not in control: Showing type mode icon.")
            if CameraWidget.type_mode:
                CameraWidget.typemode_icon.source = 'Images/TYPE_ACTIVE.png'
            else:
                CameraWidget.typemode_icon.source = 'Images/TYPE_INACTIVE.png'
                
    def navigate_direction(self, direction, type_screen):
        """Handles actions based on eye navigation input, mirroring on_key_down functionality."""
        print(f"ListWidget: Current direction: {direction}")
        # Actions for the list widget
        if self.opacity == 1:
            print(f"ListWidget visible")
            if direction == "Right":  # Right arrow key (Go to chat_widget)
                type_screen.chat()
            elif direction == "Up":  # Up arrow key (Speak out)
                type_screen.speak_user_input()
            elif direction == "Left":  # Left arrow (Go to search_widget)
                type_screen.search()
            elif direction == "Down":  # Down arrow key (exit from list widget)
                self.hide()
                type_screen.ids.go_to_list.opacity = 1
                type_screen.ids.go_to_files.opacity = 1
                type_screen.ids.go_to_menu.opacity = 1
                type_screen.ids.go_to_help.opacity = 1
        # Action for each applications
        elif type_screen.manager.current == 'type':
            print(f"{type_screen.manager.current} screen : Action for type screen applications")
            print(f"ListWidget not visible")
            chat_widget = type_screen.chat_widget
            select_chat = chat_widget.ids.select_chat
            message_label = chat_widget.ids.message_label
            file_widget = type_screen.file_widget
            # Actions for chat
            if chat_widget.opacity == 1:
                if select_chat.opacity == 0:
                    if file_widget.opacity == 1:
                        if direction == "Left":
                            type_screen.delete_content_and_update(file_widget.selected_index)
                        elif direction == "Down":
                            file_widget.move_selection_down()
                        elif direction == "Up" or direction == "Left":
                            type_screen.hide_file_widget()
                        elif direction == "Right":
                            message = file_widget.get_highlighted_text()
                            Clock.schedule_once(lambda dt: setattr(message_label, 'text', message), 0)
                            print("Message from file widget:", message)
                            type_screen.hide_file_widget()
                    # Exit from chat with Left arrow
                    elif direction == "Left":
                        select_chat.opacity = 1
                        chat_widget.clear_bubbles()
                        chat_widget.create_sender_buttons()
                    # Access files with Up arrow
                    elif direction == "Up":
                        file_widget.row = 6
                        type_screen.file_for_chat = True
                        type_screen.show_file_widget()
                        file_widget.update_highlight()
                        message_label.text = "Right to get text here"
                    # Type with Down arrow
                    elif direction == "Down":
                        type_screen.type_for_chat = True
                        chat_widget.opacity = 0
                        chat_widget.disabled = True
                    # Send with Right arrow
                    elif direction == "Right":
                        message = message_label.text.strip()
                        if message and message not in ["Down to type message","Right to get text here"]:
                            timestamp = time.time() # store Unix timestamp
                            chat_widget.send_telegram_alert(message, chat_widget.chat_id, timestamp)
                            chat_widget.save_chat_message(chat_widget.chat_id, message, timestamp, is_user = True)
                            message_label.text = "Down to type message"
                        else:
                            AlertPopup("No message to send").open()
                # When the sender selection is visible
                elif direction == "Left":
                    type_screen.hide_chat_widget()
                    self.show()
                elif direction == "Up":
                    chat_widget.navigate_senders("Up")
                elif direction == "Down":
                    chat_widget.navigate_senders("Down")
                elif direction == "Right":
                    sender = chat_widget.sender_buttons[chat_widget.selected_index].text
                    chat_id = chat_widget.chat_dict[sender]
                    message = type_screen.get_typing_widget_text()
                    chat_widget.select_chat(sender, chat_id, message)

            # Actions for search
            elif type_screen.search_widget.opacity == 1:
                if direction == "Right":
                    type_screen.hide_search_widget()
                    self.show()

            # Go back to list widget
            elif direction == "Right":
                self.show()