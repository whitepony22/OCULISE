from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image, AsyncImage
from kivy.graphics import Color, RoundedRectangle, StencilPush, StencilUse, StencilUnUse, StencilPop, Ellipse
from kivy.properties import BooleanProperty, StringProperty, NumericProperty, DictProperty, ListProperty
import os
from kivy.clock import Clock
from camera_widget import CameraWidget, Notification
import json
import traceback
import requests
import threading
import time, datetime
import key
from kivy.app import App

class ChatWidget(BoxLayout):
    
    chat_dict = DictProperty(key.chat_id)  # Example data
    sender_buttons = ListProperty([])
    selected_index = NumericProperty(0)  # Track selected button index
    chat_id = StringProperty("")
    Clock.max_iteration = 50

    def __init__(self, **kwargs):
        super(ChatWidget, self).__init__(**kwargs)
        self.opacity = 0  # Start hidden
        self.markup = True  # Enable Kivy markup
        self.disabled = True  # Start disabled
        self.bind(disabled=self.update_typemode_icon)  # Update the type mode icon when visible

        # Telegram Bot Config
        self.telegram_bot_token = key.telegram_bot_token
        self.telegram_api_url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        self.telegram_api_url_get_updates = f"https://api.telegram.org/bot{self.telegram_bot_token}/getUpdates"
        
        # Start Telegram Listener
        self.start_telegram_listener()

        self.chat_history_dir = "chat_histories"  # Directory to store chat histories
        if not os.path.exists(self.chat_history_dir):
            os.makedirs(self.chat_history_dir)
        self.processed_messages = {}

        self.profile_manager = ProfilePicManager(key.telegram_bot_token)
        threading.Thread(target=self.profile_manager.fetch_all_profile_pics, args=(self.chat_dict.values(),), daemon=True).start()

    def show(self):
        self.opacity = 1  # Make visible
        self.ids.select_chat.opacity = 1
        self.disabled = False  # Enable the widget
        self.ids.sender_name.text = ""  # Set the sender name

    def hide(self):
        self.opacity = 0  # Make hidden
        self.ids.select_chat.opacity = 0
        self.disabled = True  # Disable the widget

    def create_sender_buttons(self):
        senders_layout = self.ids.senders
        senders_layout.clear_widgets()
        self.sender_buttons = []

        for i, (sender, chat_id) in enumerate(self.chat_dict.items()):
            btn = RoundedButton(
                text=sender,
                size_hint=(1, None),
                height=70,
                halign='right',
            )

            # Define button background color
            selected_color = (0.482, 0.564, 0.612, 1) if i == 0 else (0.69, 0.647, 0.541, 1)

            # Apply unique canvas properties to each button
            with btn.canvas.before:
                btn.color_instruction = Color(*selected_color)
                btn.rounded_rect = RoundedRectangle(pos=btn.pos, size=btn.size, radius=[40])

            # Ensure the RoundedRectangle follows button size/pos
            btn.bind(size=self.update_rounded_rect, pos=self.update_rounded_rect)

            # btn.bind(on_release=lambda btn, s=sender, c=chat_id: self.select_chat(s, c))
            senders_layout.add_widget(btn)
            self.sender_buttons.append(btn)
            
            # Use the pre-fetched profile pic from the manager:
            image_path = self.profile_manager.image_paths.get(chat_id, "Images/profile_pics/default_profile.png")
            print(f"Profile pic for {sender}: {image_path}")
            btn.profile_pic = image_path
            # Create an Image widget with the fetched profile picture.
            profile_pic = AsyncImage(source=btn.profile_pic,
                        size_hint=(None, None),
                        size=(50, 50),
                        allow_stretch=True,
                        keep_ratio=True)
            # Define update_img_pos with default arguments to capture current btn and img.
            def update_img_pos(instance, value, b=btn, image=profile_pic):
                # Position the image 10 pixels from the left edge and vertically centered.
                image.pos = (b.x + 20, b.y + (b.height - image.height) / 2)
            # Bind the update function so it refreshes on button changes.
            btn.bind(pos=update_img_pos, size=update_img_pos)
            update_img_pos(btn, None)  # Set initial position
            # Bind the circular mask update to the image's pos and size.
            profile_pic.bind(pos=self.update_image_mask, size=self.update_image_mask)
            self.update_image_mask(profile_pic, None)
            btn.add_widget(profile_pic)

            select_img = Image(source='Images/SELECT_CHAT.png',
                        size_hint=(None, None),
                        size=(40, 40),
                        allow_stretch=True,
                        keep_ratio=True)
            # Define and bind an update function to keep the select image on the right.
            def update_select_img_pos(instance, value, b=btn, image=select_img):
                # Position the image 20 pixels from the right edge and vertically centered.
                image.pos = (b.width - image.width - 5, b.y + (b.height - image.height) / 2)
            btn.bind(pos=update_select_img_pos, size=update_select_img_pos)
            btn.add_widget(select_img)
            update_select_img_pos(btn, None)

        self.selected_index = 0
        self.highlight_selected()

    def update_image_mask(self, instance, value):
        # Clear previous stencil instructions
        instance.canvas.before.clear()
        instance.canvas.after.clear()
        # Draw the circular mask in the canvas.before
        with instance.canvas.before:
            StencilPush()
            Ellipse(pos=instance.pos, size=instance.size)
            StencilUse()
        # In the canvas.after, remove the stencil so drawing continues normally
        with instance.canvas.after:
            StencilUnUse()
            StencilPop()
            
    def update_rounded_rect(self, instance, value):
        """Update the position and size of the button's rounded rectangle."""
        instance.rounded_rect.pos = instance.pos
        instance.rounded_rect.size = instance.size
        
    def highlight_selected(self):
        for i, btn in enumerate(self.sender_buttons):
            new_color = (0.482, 0.564, 0.612, 1) if i == self.selected_index else (0.69, 0.647, 0.541, 1)
            btn.color_instruction.rgba = new_color

    def navigate_senders(self, direction):
        if direction == "Up":
            self.selected_index = (self.selected_index - 1) % len(self.sender_buttons)
        elif direction == "Down":
            self.selected_index = (self.selected_index + 1) % len(self.sender_buttons)
        self.highlight_selected()
        
    def select_chat(self, sender, chat_id, message):
        self.ids.select_chat.opacity = 0
        print(f"Chat with: {sender} (ID: {chat_id})")
        self.ids.sender_name.text = '           ' + sender.upper()
        self.chat_id = chat_id
        if message != '':
            self.ids.message_label.text = message
        else:
            self.ids.message_label.text = "Down to type message"
        threading.Thread(target=self.load_chat_history, args=(chat_id,), daemon=True).start()

    def load_chat_history(self, chat_id):
        file_path = os.path.join(self.chat_history_dir, f"{chat_id}.jsonl")
        processed = set()  # Set for processed message IDs
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as file:
                    for line in file:
                        # Each line is a valid JSON object
                        if line.strip():  # Skip any empty lines
                            message = json.loads(line)
                            # Schedule UI updates on the main thread
                            Clock.schedule_once(lambda dt, msg=message, cid=chat_id: self.add_message(
                                msg["text"],
                                msg.get("time", None),
                                is_user=msg["is_user"], 
                                chat_id=cid), 0)
                            # If the message has an ID, add it to the processed set
                            if "message_id" in message:
                                processed.add(message["message_id"])
            else:
                print(f"No chat history found for chat ID: {chat_id}")
            # Store the processed messages in the in-memory dictionary
            self.processed_messages[chat_id] = processed
        except Exception as e:
            print(f"Error loading chat history: {e}")
            traceback.print_exc()  # Print the full traceback for debugging

    def save_chat_message(self, chat_id, message, timestamp, message_id = None, is_user = False):
        print(f"save_chat_message called with: chat_id={chat_id}, message='{message}', timestamp={timestamp}, message_id={message_id},is_user={is_user}")
        # Define the file path for the chat history in JSON Lines format
        file_path = os.path.join(self.chat_history_dir, f"{chat_id}.jsonl")
        # Open the file in append mode and write the new message as a JSON object
        with open(file_path, "a", encoding="utf-8") as file:
            if not is_user:
                file.write(json.dumps({"message_id": message_id, "text": message, "is_user": is_user, "time": timestamp}) + "\n")
                # Update the in-memory history for this chat
                if chat_id not in self.processed_messages:
                    self.processed_messages[chat_id] = set()
                self.processed_messages[chat_id].add(message_id)
            else:
                file.write(json.dumps({"text": message, "is_user": is_user, "time": timestamp}) + "\n")
                print(f"Message from user saved to chat history for chat ID {chat_id}")

    def edit_chat_message(self, chat_id, message_id, new_text):
        file_path = os.path.join(self.chat_history_dir, f"{chat_id}.jsonl")

        if not os.path.exists(file_path):
            print(f"Chat history file for chat_id {chat_id} not found.")
            return

        updated_messages = []
        found = False

        # Read the file and update the edited message
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                msg = json.loads(line)
                if msg.get("message_id") == message_id:
                    msg["text"] = new_text  # Update the message text
                    found = True
                updated_messages.append(msg)

        if found:
            # Write the updated messages back to the file
            with open(file_path, "w", encoding="utf-8") as file:
                for msg in updated_messages:
                    file.write(json.dumps(msg) + "\n")
            print(f"Message {message_id} updated in chat {chat_id}")
        else:
            print(f"Message {message_id} not found in chat {chat_id}")

    def format_timestamp(self, ts):
        """
        Given a Unix timestamp (ts), return a human-friendly string.
        If the timestamp is for today, prefix with "Today".
        If it's yesterday, prefix with "Yesterday".
        Otherwise, use the full date.
        """
        dt = datetime.datetime.fromtimestamp(ts)
        now = datetime.datetime.now()
        if dt.date() == now.date():
            return "Today " + dt.strftime("%H:%M")
        elif dt.date() == (now.date() - datetime.timedelta(days=1)):
            return "Yesterday " + dt.strftime("%H:%M")
        else:
            return dt.strftime("%d-%m-%Y %H:%M")

    def update_typemode_icon(self, instance, value):
        if value == False:
            CameraWidget.typemode_icon.source = 'Images/DEFAULT.png'
        else:
            if CameraWidget.type_mode:
                CameraWidget.typemode_icon.source = 'Images/TYPE_ACTIVE.png'
            else:
                CameraWidget.typemode_icon.source = 'Images/TYPE_INACTIVE.png'

    def send_telegram_alert(self, message, chat_id, timestamp, reply_to_message_id=None):
        data = {
            "chat_id": chat_id,
            "text": message
        }
        if reply_to_message_id:
            data["reply_to_message_id"] = reply_to_message_id
        try:
            response = requests.post(self.telegram_api_url, data=data)
            self.add_message(f"{message}", timestamp, is_user=True)
            print(f"Telegram Response: {response.status_code}, {response.text}")  # Debugging
            return response.json()
        except Exception as e:
            print(f"Error sending Telegram alert: {e}")

    def get_telegram_messages(self):
        last_update_id = None  # Keep track of the last processed message

        while True:
            # params = {'timeout': 100, 'offset': last_update_id}
            params = {'timeout': 100}
            if last_update_id is not None:
                params['offset'] = last_update_id
            try:
                response = requests.get(self.telegram_api_url_get_updates, params=params)
                if response.status_code == 200 and "result" in response.json():
                    updates = response.json()["result"]
                    print(f"Received updates: {updates}")  # Debugging

                    if updates:
                        for update in updates:
                            # Handling new messages
                            if "message" in update:
                                last_update_id = update["update_id"] + 1
                                message_text = update["message"].get("text", "")
                                sender_name = update["message"]["from"]["first_name"]
                                chat_id = update["message"]["chat"]["id"]
                                message_id = update["message"]["message_id"]
                                timestamp = time.time()  # store Unix timestamp
                                print('sender chat_id', chat_id, '\nself.chat_id', self.chat_id)
                                # Check if this message is already processed:
                                if chat_id not in self.processed_messages:
                                    self.processed_messages[chat_id] = set()
                                if message_id in self.processed_messages[chat_id]:
                                    continue  # Skip if already processed
                                # If the ChatWidget is hidden, create a Notification with the message details
                                if self.opacity == 0:
                                    pic_url = self.profile_manager.image_paths.get(str(chat_id), "Images/profile_pics/default_profile.png")
                                    # Mark as processed immediately so it’s not handled again
                                    self.processed_messages[chat_id].add(message_id)
                                    # Define a callback function for the Notification
                                    def notification_callback(action, m=message_text, c=chat_id, mid=message_id, ts=timestamp):
                                        # Save the message to history
                                        self.save_chat_message(c, m, ts, mid, is_user=False)
                                        if action == "left":
                                            # Silently process the message:
                                            print("User pressed left on the notification.")
                                            reply_message = "✔✔ read"
                                        elif action == "right":
                                            # Perform additional actions for right arrow
                                            print("User pressed right on the notification.")
                                            App.get_running_app().sm.current = 'type'
                                            self.opacity = 1  # Show the ChatWidget
                                            self.disabled = False # Enable the widget
                                            sender = next((sender for sender, cid in key.chat_id.items() if str(cid) == str(chat_id)), "Unknown")
                                            self.select_chat(sender, str(chat_id), '')
                                            reply_message = "✔✔ read"
                                        elif action == "auto":
                                            print("Notification auto-dismissed.")
                                            reply_message = "✔ received"
                                        self.send_telegram_alert(reply_message, c, ts, reply_to_message_id=mid)
                                    # Create the Notification with the callback:
                                    Clock.schedule_once(lambda dt, m=message_text, c=chat_id, mid=message_id, ts=timestamp: 
                                        App.get_running_app().camera_widget.add_widget(
                                            Notification(message_text=m, chat_id=c, message_id=mid, 
                                                action_callback=lambda action: notification_callback(action, m, c, mid, ts), profile_pic = pic_url)
                                        ), 0) 
                                    print(f"Notification created for chat ID {chat_id}")
                                # If the ChatWidget is visible, process the message directly.
                                elif str(chat_id) == self.chat_id:
                                    # Ensure the in-memory history is loaded for the current chat
                                    if self.chat_id not in self.processed_messages:
                                        self.load_processed_messages(self.chat_id)
                                    # Process message only if it hasn’t been seen before
                                    if message_id not in self.processed_messages[self.chat_id]:
                                        if message_text:
                                            print(f"Message from {sender_name}: {message_text}")
                                            Clock.schedule_once(lambda dt, cid=chat_id: self.add_message(
                                                f"{message_text}", timestamp, is_user=False, chat_id=cid))
                                            self.save_chat_message(self.chat_id, message_text, timestamp, message_id, is_user=False)
                                            # Scroll to the end of the ScrollView
                                            Clock.schedule_once(lambda dt: setattr(self.ids.scroll_view, 'scroll_y', 0))
                                            reply_message = "✔✔ read"
                                            self.send_telegram_alert(reply_message, chat_id, timestamp, reply_to_message_id=message_id)
                                        self.processed_messages[self.chat_id].add(message_id)

                            # Handling edited messages
                            if "edited_message" in update:
                                edited_text = update["edited_message"].get("text", "")
                                chat_id = update["edited_message"]["chat"]["id"]
                                message_id = update["edited_message"]["message_id"]
                                if str(chat_id) == self.chat_id and edited_text:
                                    print(f"Edited message in chat {chat_id}: {edited_text}")
                                    self.edit_chat_message(chat_id, message_id, edited_text)
                                last_update_id = update["update_id"] + 1

            except Exception as e:
                print(f"Error getting Telegram messages: {e}")

            time.sleep(2)  # Polling delay to avoid hammering the Telegram API

    def start_telegram_listener(self):
        try:
            telegram_thread = threading.Thread(target=self.get_telegram_messages)
            telegram_thread.daemon = True
            telegram_thread.start()
        except Exception as e:
            print(f"[ERROR] Starting telegram listener: {e}")

    def add_message(self, message, time, is_user = False, chat_id = None):
        """Adds a rounded chat bubble to the chat UI."""
        print(f"Adding message: {message}, is_user: {is_user}, chat_id: {chat_id}")  # Debugging print
        chat_box = self.ids.chat_box
        bubble = ChatBubble(text=message, is_user=is_user, size_hint_x = 0.68, time=self.format_timestamp(time))
        #Fetch profile pic
        if chat_id:
            image_path = self.profile_manager.image_paths.get(str(chat_id), "Images/profile_pics/default_profile.png")
            print(f"Profile pic for {chat_id}: {image_path} from {self.profile_manager.image_paths}")
            bubble.profile_pic = image_path
        chat_box.add_widget(bubble)
        chat_box.height += bubble.height + 10  # Adjust height for scrolling
        # Scroll to the end of the ScrollView
        Clock.schedule_once(lambda dt: setattr(self.ids.scroll_view, 'scroll_y', 0))

    def clear_bubbles(self):
        self.ids.chat_box.clear_widgets()

class ChatBubble(Label):
    """Custom chat bubble with rounded edges."""
    is_user = BooleanProperty(False)  # Determines message alignment and color
    profile_pic = StringProperty("Images/profile_pics/default_profile.png")  # Profile picture path
    time = StringProperty("12:00 06-03-2025")  # Message timestamp

class ProfilePicManager:
    PROFILE_DIR = "Images/profile_pics/"

    def __init__(self, bot_token):
        self.bot_token = bot_token
        # Dictionary to store fetched image URLs by chat_id
        self.image_paths = {}

    def get_profile_pic(self, chat_id):
        """
        Returns a direct download URL for the user's Telegram profile pic,
        or a local default path if no profile pic is found.
        """
        print(f"Fetching profile pic URL for chat ID {chat_id}")

        # If we already have a URL, return it
        if chat_id in self.image_paths:
            return self.image_paths[chat_id]

        try:
            # 1) Get user profile photos
            url = f"https://api.telegram.org/bot{self.bot_token}/getUserProfilePhotos?user_id={chat_id}"
            print(f"Attempting to fetch profile pic for chat ID {chat_id}")
            response = requests.get(url, timeout=5).json()

            # If not ok, or no photos, use default
            if not response.get("ok"):
                print(f"Error: Response not ok for chat ID {chat_id}")
                self.image_paths[chat_id] = "Images/profile_pics/default_profile.png"
                return self.image_paths[chat_id]

            total_count = response.get("result", {}).get("total_count", 0)
            if total_count == 0:
                print(f"No profile pic found for chat ID {chat_id}")
                self.image_paths[chat_id] = "Images/profile_pics/default_profile.png"
                return self.image_paths[chat_id]

            photos = response["result"]["photos"]
            if not photos:
                print(f"No profile pic found for chat ID {chat_id}")
                self.image_paths[chat_id] = "Images/profile_pics/default_profile.png"
                return self.image_paths[chat_id]

            # 2) Extract file_id from the largest photo
            file_id = photos[0][-1]["file_id"]

            # 3) Get file info (file_path)
            file_info_url = f"https://api.telegram.org/bot{self.bot_token}/getFile?file_id={file_id}"
            file_info = requests.get(file_info_url, timeout=5).json()
            print("Getting the profile pic info...")

            if not file_info.get("ok"):
                print(f"Failed to get file info for chat ID {chat_id}: {file_info}")
                self.image_paths[chat_id] = "Images/profile_pics/default_profile.png"
                return self.image_paths[chat_id]

            # 4) Construct the final download URL
            file_path = file_info["result"]["file_path"]
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            print(f"Profile pic URL for chat ID {chat_id}: {download_url}")

            # 5) Store the URL in image_paths
            self.image_paths[chat_id] = download_url
            return download_url

        except Exception as e:
            print(f"[ERROR] Getting profile pic for chat ID {chat_id}: {e}")
            self.image_paths[chat_id] = "Images/profile_pics/default_profile.png"
            return self.image_paths[chat_id]

        
    def fetch_all_profile_pics(self, chat_ids):
        for chat_id in chat_ids:
            self.get_profile_pic(chat_id)

class RoundedButton(Button):
    # Set a default image (you can change this later)
    profile_pic = StringProperty("Images/profile_pics/default_profile.png")