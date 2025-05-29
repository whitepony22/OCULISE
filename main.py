# main.py
from kivy.app import App
from home_screen import HomeScreen
from iot_screen import IoTScreen    
from help_screen import HelpScreen
from type_screen import TypeScreen
from camera_widget import CameraWidget
from balloon_pop import BalloonPopGame
from rain_catcher import RainGame
from word_game import WordGame
from option_screen import OptionScreen
from news_screen import NewsScreen

from kivy.uix.screenmanager import ScreenManager
from kivy.uix.floatlayout import FloatLayout

class ProjectApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name='home'))
        sm.add_widget(IoTScreen(name='iot'))
        sm.add_widget(TypeScreen(name='type'))
        sm.add_widget(HelpScreen(name='help'))
        sm.add_widget(OptionScreen(name='option'))
        sm.add_widget(BalloonPopGame(name='balloon'))
        sm.add_widget(RainGame(name='rain'))
        sm.add_widget(WordGame(name='word'))
        sm.add_widget(NewsScreen(name='news'))
        self.sm = sm
        sm.current = 'home'  # Set the default screen to main

        # Create the main layout
        root = FloatLayout(orientation='vertical')

        # Add the ScreenManager to the layout
        root.add_widget(sm)

        # Create and add the CameraWidget, make it float on top
        self.camera_widget = CameraWidget(sm) #, size_hint=(0.3, 0.3), pos_hint={'x': 0.5, 'y': 0.5})
        root.add_widget(self.camera_widget)

        # Start the countdown when the app launches
        self.camera_widget.start_countdown()  # Start countdown to capture

        return root

if __name__ == '__main__':
    ProjectApp().run()