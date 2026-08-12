import math
import requests
import threading
from datetime import datetime

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line
from kivy.clock import Clock
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.metrics import dp

Window.clearcolor = (1,1,1,1)

Cities = {
    "Екатеринбург": {"lat":56.84, "lon": 60.61},
    "Сысерть": {"lat":56.50, "lon":60.81},
    "Киров": {"lat":58.60, "lon": 49.66}

}

class WeatherCanvas(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.timer=None
        self.current_weather = "loader"
        self.bind(pos=self.redraw, size=self.redraw)
        self.start_loader()

    def redraw(self, *args):
        if self.current_weather =="loader":
            self.draw_sun_loader(rotating=True if self.timer else False)
        elif self.current_weather =="sun":
            self.draw_sun_loader(rotating=False)
        elif self.current_weather =="cloud":
            self.draw_cloud()
        elif self.current_weather == "rain":
            self.draw_rain()

    def draw_sun_loader(self, rotating=False):
        self.current_weather = 'loader' if rotating else "sun"
        self.canvas.clear()
        cx, cy =self.center_x, self.center_y
        r_sun = dp(45)
        ray_dist = dp(55)
        ray_len = dp(20)

        with self.canvas:
            Color(1, 0.75, 0)
            Ellipse(pos=(cx - r_sun, cy - r_sun), size=(r_sun * 2, r_sun * 2))

            for i in range(8):
                offset = self.angle if rotating else 0
                rad = math.radians(offset + i *45)
                x1 = cx + ray_dist * math.cos(rad)
                y1 = cy + ray_dist * math.sin(rad)
                x2 = cx + (ray_dist + ray_len) * math.cos(rad)
                y2 = cy + (ray_dist + ray_len) * math.sin(rad)
                Line(points=[x1,y1,x2,y2], width=dp(4), cap='round')

    def animation_loader(self, dt):
        self.angle = (self.angle +4)%360
        self.draw_sun_loader(rotating=True)

    def stop_loader(self):
        if self.timer:
            self.timer.cancel()
            self.timer =None

    def start_loader(self):
        self.stop_loader()
        self.timer = Clock.schedule_interval(self.animation_loader, 0.03)

    def draw_cloud(self):
        self.current_weather = 'cloud'
        self.canvas.clear()
        cx,cy= self.center_x, self.center_y
        with self.canvas:
            Color(0.75, 0.8, 0.85)
            Ellipse(pos=(cx-dp(120),cy - dp(30)), size=(dp(100),dp(100)))
            Ellipse(pos=(cx-dp(60),cy - dp(30)), size=(dp(100),dp(100)))
            Ellipse(pos=(cx+dp(5),cy-dp(30)), size=(dp(100),dp(100)))
            Ellipse(pos=(cx+dp(55),cy-dp(30)), size=(dp(100),dp(100)))
            Ellipse(pos=(cx+dp(10),cy+dp(20)), size=(dp(120),dp(120)))
            Ellipse(pos=(cx-dp(60),cy+dp(20)),size=(dp(95),dp(95)))

    def update_animation(self,dt):
        self.angle = (self.angle + 3) % 360
        self.draw_sun_loader()

    def draw_rain(self):
        self.current_weather= 'rain'
        self.draw_cloud()
        cx,cy= self.center_x, self.center_y
        with self.canvas:
            Color(0.3, 0.6, 0.9)
            Line(points=[cx - dp(75), cy - dp(50), cx - dp(90), cy - dp(95)], width=dp(6), cap='round')
            Line(points=[cx - dp(15), cy - dp(50), cx - dp(30), cy - dp(95)], width=dp(6), cap='round')
            Line(points=[cx + dp(45), cy - dp(50), cx + dp(30), cy - dp(95)], width=dp(6), cap='round')
            Line(points=[cx + dp(105), cy - dp(50), cx + dp(90), cy - dp(95)], width=dp(6), cap='round')

def draw_storm(self):
        self.current_weather = 'storm'
        self.draw_rain()
        cx,cy= self.center_x, self.center_y
        with self.canvas:
            Color(1, 0.8, 0)
            Line(points=[cx+dp(15),cy-dp(30),cx-dp(15),cy-dp(75),cx+dp(25),cy-dp(75),cx-dp(5),cy-dp(125)], width=dp(4), cap='square', joint='miter')


class WeatherApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=50,spacing=20)

        self.city_spinner = Spinner(
            text="Екатеринбург",
            values=list(Cities.keys()),
            size_hint=(1,None),
            height="45dp"
        )
        self.city_spinner.bind(text=self.on_city_changed)
        main_layout.add_widget(self.city_spinner)

        self.weather_canvas = WeatherCanvas(size_hint=(1,0.45))
        main_layout.add_widget(self.weather_canvas)

        self.status_label = Label(
            text="Загрузка...",
            color=(0.2,0.2,0.2,1),
            font_size="22sp",
            size_hint=(1, 0.15),
            halign="center"
        )
        main_layout.add_widget(self.status_label)
        scroll_view = ScrollView(
            size_hint=(1,0.3),
            do_scroll_x=True,
            do_scroll_y=False
        )
        self.hourly_layout = BoxLayout(orientation="horizontal", size_hint_x=None, spacing=10, padding=5)
        self.hourly_layout.bind(minimum_width=self.hourly_layout.setter('width'))
        scroll_view.add_widget(self.hourly_layout)
        main_layout.add_widget(scroll_view)

        self.load_weather_data()
        return main_layout


    def get_weather(self, lat, lon):
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,weather_code&"
            f"hourly=temperature_2m,weather_code&"
            f"forecast_days=2&"
            f"timezone=auto"
        )
        responce = requests.get(url)
        data = responce.json()

        current_temp = data["current"]["temperature_2m"]
        current_code = data["current"]["weather_code"]

        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        codes= data["hourly"]["weather_code"]

        now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
        start_index = 0
        if now_str in times:
            start_index = times.index(now_str)
        hourly_24=[]
        for i in range(start_index, min(start_index+24, len(times))):
            time_obj = datetime.strptime(times[i], "%Y-%m-%dT%H:%M")
            hour_label = time_obj.strftime("%H:%M")

            hourly_24.append({
                "time": hour_label,
                "temp": round(temps[i]),
                "code":codes[i]
            })
        return{
            "current_temp": current_temp,
            "current_code": current_code,
            "hourly": hourly_24
        }

    def update_ui(self, data):
        self.weather_canvas.stop_loader()

        temp = data["current_temp"]
        code = data["current_code"]
        if code in [0,1]:
            self.weather_canvas.draw_sun_loader(rotating=False)
            weather_text="Солнечно"

        elif code in [2,3,45,48]:
            self.weather_canvas.draw_cloud()
            weather_text="Облачно"

        elif code in [95,96,99]:
            self.draw_storm()
            weather_text="Гроза"

        else:
            self.weather_canvas.draw_rain()
            weather_text = "Дождь"

        self.status_label.text = f"{temp}°C | {weather_text}"

        self.hourly_layout.clear_widgets()
        for item in data["hourly"]:
            card = self.create_hour_card(item["time"], item["temp"], item["code"])
            self.hourly_layout.add_widget(card)

    def on_city_changed(self, spinner, text):
        self.weather_canvas.start_loader()
        self.status_label.text="Загрузка..."
        self.hourly_layout.clear_widgets()
        self.load_weather_data()

    def load_weather_data(self):
        selected_city = self.city_spinner.text
        coords = Cities[selected_city]
        threading.Thread(target=self.fetch_in_background, args=(coords["lat"], coords["lon"]), daemon = True).start()

    def fetch_in_background(self, lat, lon):
        try:
            weather_data = WeatherApp.get_weather(self, lat, lon)
            Clock.schedule_once(lambda dt: self.update_ui(weather_data))
        except Exception as e:
            print("Ошибка загрузки", e)
            Clock.schedule_once(lambda dt: self.show_error())

    def create_hour_card(self, time_str, temp, code):
        card = BoxLayout(
            orientation = 'vertical',
            size_hint=(None, 1),
            width="65dp",
            padding = 5,
            spacing=2
        )
        icon_file = "sun.png" if code in [0, 1] else ("cloud.png" if code in [2,3,45,48] else("groza.png" if code in [95,96,99] else "rain.png"))
        lbl_time = Label(text=time_str, font_size="12sp", color=(0.4,0.4,0.4,1))
        img_icon=Image(source=icon_file,size_hint=(1,1))
        lbl_temp = Label(text=f"{temp}°C", font_size="14sp", bold=True, color=(0.2,0.2,0.2,1))

        card.add_widget(lbl_time)
        card.add_widget(img_icon)
        card.add_widget(lbl_temp)

        return card

    def show_error(self):
        self.weather_canvas.stop_loader()
        self.status_label.text =  "Нет соединения(возможно код корявый¯\_(ツ)_/¯"
if __name__ == '__main__':
    WeatherApp().run()