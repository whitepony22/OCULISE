from kivy.uix.boxlayout import BoxLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.clock import Clock
import re
import threading
from kivy.clock import mainthread
#pip install google.generativeai
import google.generativeai as genai
import key
from camera_widget import CameraWidget

class SearchWidget(BoxLayout):
    
    def __init__(self, **kwargs):
        super(SearchWidget, self).__init__(**kwargs)
        self.opacity = 0  # Start hidden
        self.markup = True  # Enable Kivy markup
        self.disabled = True  # Start disabled
        self.bind(disabled=self.update_typemode_icon)  # Update the type mode icon when visible
        
    def show(self):
        self.opacity = 1  # Make visible
        self.disabled = False  # Enable the widget
        
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

    def on_search(self, query):
        words = query.split()
        display_text = ' '.join(words[:4]) + (' ...' if len(words) > 3 else '') # Display the first 4 words
        self.ids.search_query.text = display_text  # Update the search query text
        self.ids.search_result.text = ""  # Clear the previous result
        self.show_loading_indicator()  # Call the function to show the popup

        def run_query():
            try:
                genai.configure(api_key=key.gemini_key)
                model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")
                response = model.generate_content(f"{query}\n\nPlease limit within 150 words.")
                result_text = self.format_text(str(response.text))  # Store the result
                print(result_text)
            except Exception as e:
                result_text = f"Error: {e}"
                print(f"Gemini API Error: {e}")
            finally:
                self.hide_loading_indicator(result_text)  # Pass the result

        thread = threading.Thread(target=run_query)
        thread.start()

    def show_loading_indicator(self):
        self.ids.loading_image.opacity = 1

    @mainthread
    def hide_loading_indicator(self, result_text):
        self.ids.loading_image.opacity = 0
        Clock.schedule_once(lambda dt: self.typewriter_animation(self.ids.search_result, result_text), 1)  # Start animation after 1s
        # self.ids.search_result.text = result_text

    def format_text(self, text):
        """Converts markdown-like syntax to Kivy markup."""
        # Convert **bold** to [b]bold[/b]
        text = re.sub(r'\*\*(.*?)\*\*', r'[b]\1[/b]', text)
        # Convert *italic* to [i]italic[/i]
        text = re.sub(r'\*(.*?)\*', r'[i]\1[/i]', text)
        # Convert - to bullet points
        text = re.sub(r'^\s*\*\s*(.*)', r'• \1', text, flags=re.MULTILINE) 
        return text
    
    def typewriter_animation(self, widget, text, delay=0.1, line_delay=0.5):
        """
        Animates text line by line in a Kivy Label.
        - `widget`: The Kivy Label where text is displayed.
        - `text`: The full text to display (processed with `format_text`).
        - `delay`: Delay between characters (default: 0.1s).
        - `line_delay`: Delay before starting the next line (default: 1.5s).
        """
        lines = text.split("\n")  # Split text into lines
        widget.text = ""  # Clear label
        widget.markup = True  # Enable Kivy markup
        widget.current_index = 0

        def display_next_line(dt):
            if widget.current_index < len(lines):
                widget.text += lines[widget.current_index] + "\n"  # Append next line
                widget.current_index += 1
                # scroll_to_end()  # Scroll to the label after adding text
                Clock.schedule_once(type_line, delay)  # Start typewriter effect

        def type_line(dt):
            if widget.current_index <= len(lines):
                Clock.schedule_once(display_next_line, line_delay)  # Delay between lines

        # This method ensures we scroll the ScrollView after the specific line is reached
        def scroll_to_end():
            print(widget.parent)
            if widget.parent:  # Ensure the widget has a parent before accessing the ScrollView
                widget.parent.scroll_to(widget, padding=10)  # Scroll to the label

        display_next_line(0)  # Start animation

    