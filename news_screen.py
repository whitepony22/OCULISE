import requests
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen, SlideTransition
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from camera_widget import CameraWidget, Notification
from bs4 import BeautifulSoup
import threading
import asyncio
import aiohttp
import key

# Replace with your actual NewsAPI key from key.py
NEWS_API_KEY = key.newsapi_key
NEWS_API_URL = f"https://newsapi.org/v2/top-headlines?category=general&apiKey={NEWS_API_KEY}"

class NewsScreen(Screen):
    selected_index = NumericProperty(-1)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(lambda dt: self.start_fetch_news_thread(), 300)
        self.start_fetch_news_thread()  # Immediately fetch on startup

    def start_fetch_news_thread(self):
        threading.Thread(target=self.fetch_news, daemon=True).start()

    def on_enter(self):
        Window.bind(on_key_down=self.on_key_down)
        # Reset scroll position to top
        self.ids.scroll_view.scroll_y = 1.0
        CameraWidget.camera_layout.pos_hint = {"y": 0, "x": 0}

    def on_leave(self):
        Window.unbind(on_key_down=self.on_key_down)
        self.selected_index = -1
        # Update highlight (clear all highlights)
        articles = self.ids.news_layout.children[::-1]
        self.update_highlight(articles)

    def fetch_news(self, dt):
        try:
            response = requests.get(NEWS_API_URL)
            data = response.json()
            articles = data.get("articles", [])
            
            news_layout = self.ids.news_layout
            news_layout.clear_widgets()
            
            if articles:
                for article in articles:
                    title = article.get("title", "No Title")
                    description = article.get("description", "") or ""
                    image_source = article.get("urlToImage", "") or ""
                    short_description = description[:200] + "..." if len(description) > 200 else description
                    url = article.get("url", "")
                    # Create an ArticleButton with the article data
                    btn = ArticleButton(title=title, description=description, image_source=image_source, short_description=short_description)
                    news_layout.add_widget(btn)
                    # Start fetching the full article in the background
                    threading.Thread(target=self.run_fetch_full_content, args=(url,btn), daemon=True).start()
            else:
                news_layout.add_widget(
                    ArticleButton(title="No articles found.", description="", image_source="")
                )
        except Exception as e:
            news_layout = self.ids.news_layout
            news_layout.clear_widgets()
            news_layout.add_widget(
                ArticleButton(title=f"Error: {str(e)}", description="", image_source="")
            )

    def run_fetch_full_content(self, url, btn):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        full_article = loop.run_until_complete(self.fetch_full_content(url))
        loop.close()
        # Update the button’s description on the main thread once the full article is fetched
        Clock.schedule_once(lambda dt: setattr(btn, 'description', full_article))

    async def fetch_full_content(self, url):
        if not url:
            return ""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, 'html.parser')
                        paragraphs = soup.find_all('p')
                        full_article = "\n".join([p.get_text() for p in paragraphs])
                        return full_article
        except Exception as e:
            print(f"Error fetching full article: {e}")
        return ""

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
        news_layout = self.ids.news_layout
        articles = news_layout.children[::-1]

        if self.manager and direction in CameraWidget.transition_map:
            self.manager.transition = SlideTransition(direction=CameraWidget.transition_map[direction])
        if self.manager.current == 'news' and not Notification.is_active:
            if self.ids.article_detail.opacity == 1:
                if direction == "Left":
                    self.ids.article_detail.hide()
                elif direction == "Up":
                    article_content = self.ids.article_detail.ids.article_content
                    if article_content.scroll_y < 1:
                        article_content.scroll_y = min(article_content.scroll_y + 0.1, 1)
                elif direction == "Down":
                    article_content = self.ids.article_detail.ids.article_content
                    if article_content.scroll_y > 0:
                        article_content.scroll_y = max(article_content.scroll_y - 0.1, 0)
            elif direction == "Up":
                self.manager.current = 'option'
            elif direction == "Down":
                if self.selected_index < len(articles) - 1:
                    self.selected_index += 1
                else:
                    self.selected_index = 0
                self.update_highlight(articles)
            elif direction == "Left":
                self.selected_index = 0
                self.update_highlight(articles)
            elif direction == "Right" and self.selected_index != -1:
                article = articles[self.selected_index]
                self.ids.article_detail.show()
                self.ids.article_detail.load_article(
                    article.title,
                    article.description,
                    article.image_source)
                self.ids.article_detail.ids.article_content.scroll_y = 1

    def update_highlight(self, articles):
        for i, article in enumerate(articles):
            article.selected = (i == self.selected_index)
        if 0 <= self.selected_index < len(articles):
            current_article = articles[self.selected_index]
            # Scroll to the top when the first article is selected
            if self.selected_index == 0:
                self.ids.scroll_view.scroll_y = 1
            # Center after halfway
            elif self.selected_index * current_article.height > self.ids.scroll_view.height / 2.5:
                target_y = current_article.y - (self.ids.scroll_view.height / 2) + (current_article.height / 2)
                self.ids.scroll_view.scroll_y = target_y / (self.ids.news_layout.height - self.ids.scroll_view.height)
            print(f"Current highlighted article index: {self.selected_index} | Title: {current_article.title}")

class ArticleButton(ButtonBehavior, BoxLayout):
    title = StringProperty("")
    description = StringProperty("")
    short_description = StringProperty("")
    image_source = StringProperty("")
    selected = BooleanProperty(False) 

    def on_press(self):
        # You can add logic here to show the full article,
        # for example opening a new screen or a popup.
        print("Article pressed:", self.title)

    def on_selected(self, instance, value):
        print(f"[DEBUG] on_selected triggered for '{self.title}': value = {value}")
        # print(f"[DEBUG] Canvas.before.children: {self.canvas.before.children}")
        if self.canvas.before.children:
            # Assuming the first instruction is the Color instruction
            if value:
                self.canvas.before.children[0].rgba = (0.8, 0.8, 1, 1)  # Highlighted
                print(f"[DEBUG] Set highlighted color for '{self.title}'")
            else:
                self.canvas.before.children[0].rgba = (0.95, 0.95, 0.95, 1)  # Default
                print(f"[DEBUG] Set default color for '{self.title}'")

class ArticleDetailWidget(FloatLayout):
    title = StringProperty("")
    description = StringProperty("")
    image_source = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.opacity = 0  # Start hidden
        self.disabled = True  # Start disabled

    def show(self):
        self.opacity = 1  # Make visible
        self.disabled = False  # Enable the widget
        
    def hide(self):
        self.opacity = 0  # Make hidden
        self.disabled = True  # Disable the widget

    def load_article(self, title, description, image_source):
        self.title = title
        self.description = description
        self.image_source = image_source