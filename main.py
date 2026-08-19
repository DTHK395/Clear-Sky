import math
import urllib.request
import json
import threading
import traceback
import os
from datetime import datetime
try:
    import ssl
    has_ssl = True
except Exception:
    has_ssl=False

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.clock import Clock
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.metrics import dp
from kivy.utils import platform
from plyer import gps

Window.clearcolor = (1,1,1,1)

Cities = {
    "Екатеринбург": {"lat":56.84, "lon": 60.61},
    "Сысерть": {"lat":56.50, "lon":60.81},
    "Киров": {"lat":58.60, "lon": 49.66},
    "посёлок Чамзинка": {"lat":54.40, "lon":45.78},
    "Южноуральск": {"lat":54.44,"lon":61.26}

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
        elif self.current_weather == "moon":
            self.draw_moon()

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

    def draw_moon(self):
        self.current_weather='moon'
        self.canvas.clear()
        cx,cy= self.center_x, self.center_y
        r_moon = dp(70)
        with self.canvas:
            Color(0.9,0.9,0.6)
            Ellipse(pos=(cx-r_moon,cy - r_moon), size=(r_moon*2,r_moon*2))
            Color(1,1,1)
            Ellipse(pos=(cx-r_moon+dp(15),cy-r_moon+dp(10)), size=(r_moon*2,r_moon*2))

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

BURGUNDY_COLOR=(0.45, 0.05, 0.15, 1)

class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0,0,0,0)
        self.color= (0.2,0.2,0.2,1)

        with self.canvas.before:
            self.bg_color= Color(1,1,1,1)
            self.bg_rect = RoundedRectangle(radius=[dp(15)])
            self.border_color = Color(*BURGUNDY_COLOR)
            self.border_line=Line(width=dp(1.5))

        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.on_state)

    def update_canvas(self, *args):
        pad=dp(2)
        self.bg_rect.pos=(self.x + pad, self.y+pad)
        self.bg_rect.size=(self.width - pad*2, self.height - pad*2)
        self.border_line.rounded_rectangle=(self.x+pad,self.y+pad,self.width-pad*2,self.height-pad*2, dp(15))

    def on_state(self, instance, value):
        self.bg_color.rgba=(0.9,0.9,0.9,1) if value == 'down' else (1,1,1,1)

class RoundedSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal=''
        self.background_down=''
        self.background_color = (0,0,0,0)
        self.color= (0.2,0.2,0.2,1)
        with self.canvas.before:
            self.bg_color= Color(1,1,1,1)
            self.bg_rect = RoundedRectangle(radius=[dp(10)])
            self.border_color = Color(*BURGUNDY_COLOR)
            self.border_line=Line(width=dp(1.2))

        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.on_state)

    def update_canvas(self, *args):
        pad=dp(2)
        self.bg_rect.pos=(self.x + pad, self.y+pad)
        self.bg_rect.size=(self.width - pad*2, self.height - pad*2)
        self.border_line.rounded_rectangle=(self.x+pad,self.y+pad,self.width-pad*2,self.height-pad*2, dp(10))

    def on_state(self, instance, value):
        self.bg_color.rgba=(0.9,0.9,0.9,1) if value == 'down' else (1,1,1,1)

class RoundedSpinner(Spinner):
    def __init__(self, **kwargs):
        kwargs['option_cls']=RoundedSpinnerOption
        super().__init__(**kwargs)
        self.background_normal=''
        self.background_down=''
        self.background_color = (0,0,0,0)
        self.color= (0.2,0.2,0.2,1)
        with self.canvas.before:
            self.bg_color= Color(1,1,1,1)
            self.bg_rect = RoundedRectangle(radius=[dp(15)])
            self.border_color = Color(*BURGUNDY_COLOR)
            self.border_line=Line(width=dp(1.5))

        self.bind(pos=self.update_canvas, size=self.update_canvas, state=self.on_state)

    def update_canvas(self, *args):
        pad=dp(2)
        self.bg_rect.pos=(self.x + pad, self.y+pad)
        self.bg_rect.size=(self.width - pad*2, self.height - pad*2)
        self.border_line.rounded_rectangle=(self.x+pad,self.y+pad,self.width-pad*2,self.height-pad*2, dp(15))

    def on_state(self, instance, value):
        self.bg_color.rgba = (0.9, 0.9, 0.9, 1) if value == 'down' else (1, 1, 1, 1)

class WeatherApp(App):
    def get_settings_path(self):
        return os.path.join(self.user_data_dir, "settings.json")

    def save_last_city(self,city):
        try:
            with open(self.get_settings_path(), "w", encoding='utf-8')as f:
                json.dump({"last_city":city}, f)
        except Exception:
            pass
        return "Екатеринбург"

    def load_last_city(self):
        try:
            if os.path.exists(self.get_settings_path()):
                with open(self.get_settings_path(), 'r', encoding="utf-8") as f:
                    data = json.load(f)
                    saved_city= data.get("last_city", "Екатеринбург")

                    if saved_city not in Cities and saved_city != "Моё местоположение":
                        return "Екатеринбург"
                    return saved_city
        except Exception:
            pass
        return "Екатеринбург"

    def on_start(self):
        try:
            if platform=="android":
                from android.permissions import request_permissions, Permission
                request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION])
        except Exception as e:
            self.status_label.text=f"Ошибка разрешений: {e}"
            self.status_label.font_size = "12sp"

    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=50,spacing=20)

        last_city=self.load_last_city()
        self.city_spinner = RoundedSpinner(
            text=last_city,
            values=["Моё местоположение"] + list(Cities.keys()),
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
            halign="center",
            valign="middle"
        )
        self.status_label.bind(size=lambda instance, size: setattr(instance, "text_size", (size[0],None)))
        main_layout.add_widget(self.status_label)

        self.gps_btn=RoundedButton(text="Поиск по GPS", markup=True, background_color=(0,0,0,0), color=(0.2,0.2,0.2,1),font_size='14sp',size_hint=(1,None),height='0dp',opacity=0,disabled=True)
        self.gps_btn.bind(on_release=lambda x: self.gps_geolocation())
        main_layout.add_widget(self.gps_btn)
        scroll_view = ScrollView(
            size_hint=(1,0.3),
            do_scroll_x=True,
            do_scroll_y=False
        )
        self.hourly_layout = BoxLayout(orientation="horizontal", size_hint_x=None, spacing=10, padding=5)
        self.hourly_layout.bind(minimum_width=self.hourly_layout.setter('width'))
        scroll_view.add_widget(self.hourly_layout)
        main_layout.add_widget(scroll_view)

        self.on_city_changed(self.city_spinner,last_city)
        return main_layout


    def get_weather(self, lat, lon):
        if not has_ssl:
            raise Exception("No SSL")
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&"
            f"current=temperature_2m,weather_code,is_day&"
            f"hourly=temperature_2m,weather_code,is_day&"
            f"forecast_days=2&"
            f"timezone=auto"
        )
        ctx = ssl._create_unverified_context()
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, context=ctx) as response:
            data = json.loads(response.read().decode('utf-8'))

        current_temp = data["current"]["temperature_2m"]
        current_code = data["current"]["weather_code"]
        current_is_day= data["current"]["is_day"]

        times = data["hourly"]["time"]
        temps = data["hourly"]["temperature_2m"]
        codes= data["hourly"]["weather_code"]
        is_day= data["hourly"]["is_day"]

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
                "code":codes[i],
                "is_day":is_day[i]
            })
        return{
            "current_temp": current_temp,
            "current_code": current_code,
            "hourly": hourly_24,
            "current_is_day": current_is_day
        }

    def update_ui(self, data):
        self.weather_canvas.stop_loader()
        self.status_label.font_size="22sp"

        temp = data["current_temp"]
        code = data["current_code"]
        is_day = data["current_is_day"]
        if code in [0,1]:
            if is_day==1:
                self.weather_canvas.draw_sun_loader(rotating=False)
                weather_text="Солнечно"
            else:
                self.weather_canvas.draw_moon()
                weather_text="Безоблачная ночь"

        elif code in [2,3,45,48]:
            self.weather_canvas.draw_cloud()
            weather_text="Облачно"

        elif code in [95,96,99]:
            self.weather_canvas.draw_storm()
            weather_text="Гроза"

        else:
            self.weather_canvas.draw_rain()
            weather_text = "Дождь"

        self.status_label.text = f"{temp}°C | {weather_text}"

        self.hourly_layout.clear_widgets()
        for item in data["hourly"]:
            card = self.create_hour_card(item["time"], item["temp"], item["code"], item["is_day"])
            self.hourly_layout.add_widget(card)

    def on_city_changed(self, spinner, text):
        self.save_last_city(text)
        self.weather_canvas.start_loader()
        self.hourly_layout.clear_widgets()
        if text == "Моё местоположение":
            self.gps_btn.height="45dp"
            self.gps_btn.opacity=1
            self.gps_btn.disabled = False

            self.status_label.text = "Быстрый поиск(по IP)..."
            threading.Thread(target=self.IP_geolocation, daemon=True).start()
        else:
            self.gps_btn.height="0dp"
            self.gps_btn.opacity=0
            self.gps_btn.disabled = True

            self.status_label.text = "Загрузка..."
            self.load_weather_data()

    def get_geolocations(self):
        self.status_label.text="Быстрый поиск геолокации...(по IP)"
        threading.Thread(target=self.IP_geolocation, daemon=True).start()

    def IP_geolocation(self):
        ctx =ssl._create_unverified_context()
        headers={"User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

        try:
            req=urllib.request.Request("https://ipwho.is/",headers=headers)
            with urllib.request.urlopen(req,context=ctx,timeout=5) as responce:
                data=json.loads(responce.read().decode('utf-8'))

            if data.get("success"):
                lat=data["latitude"]
                lon=data["longitude"]
                weather_data=self.get_weather(lat, lon)
                Clock.schedule_once(lambda dt:self.update_ui(weather_data))
                return
        except Exception:
            pass

        try:
            req = urllib.request.Request("http://ip-api.com/json/", headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as responce:
                data = json.loads(responce.read().decode('utf-8'))

            if data.get("status") == "success":
                lat = data["lat"]
                lon = data["lon"]
                weather_data = self.get_weather(lat, lon)
                Clock.schedule_once(lambda dt: self.update_ui(weather_data))
                return
        except Exception:
            pass

        Clock.schedule_once(lambda dt: self.gps_geolocation())

    def gps_geolocation(self):
        try:
            gps.configure(on_location=self.geolocations, on_status=self.on_gps_status)
            gps.start(1000,0)
            self.status_label.text="Поиск спутников GPS... \n(в помещении данный процесс может затянуться)"
            self.status_label.font_size="14sp"
            self.gps_timer=Clock.schedule_once(self.gps_timeout, 30)
        except Exception as e:
            self.status_label.text="GPS данные не получены"
            self.weather_canvas.stop_loader()

    def on_gps_status(self, general_status, status_message):
        if general_status=='provider-disabled':
            if hasattr(self, "gps_timer"):
                Clock.unschedule(self.gps_timer)
            try:
                gps.stop()
            except:
                pass
            Clock.schedule_once(lambda dt: self.show_error("Включите геолокацию в шторке телефона"))

    def geolocations(self,**kwargs):
        if hasattr(self,"gps_timer"):
            Clock.unschedule(self.gps_timer)
        try:
            gps.stop()
        except:
            pass

        lat=kwargs.get("lat")
        lon=kwargs.get("lon")

        if lat and lon:
            threading.Thread(target=self.fetch_in_background, args=(lat,lon), daemon=True).start()
        else:
            Clock.schedule_once(lambda dt: self.show_error("GPS вернул пустые координаты"))


    def gps_timeout(self, dt):
        try:
            gps.stop()
        except:
            pass
        self.show_error("Не удалось получить данные GPS(попробуйте подойти к окну или выйти на балкон)")

    def load_weather_data(self):
        selected_city=self.city_spinner.text

        if selected_city not in Cities:
            selected_city="Екатеринбург"
            self.city_spinner.text=selected_city
        selected_city = self.city_spinner.text
        coords = Cities[selected_city]
        threading.Thread(target=self.fetch_in_background, args=(coords["lat"], coords["lon"]), daemon = True).start()

    def fetch_in_background(self, lat, lon):
        try:
            weather_data = WeatherApp.get_weather(self, lat, lon)
            Clock.schedule_once(lambda dt: self.update_ui(weather_data))
        except Exception:
            err_msg = "Нет соединения\n(возможно код корявый ¯\(o_o)/¯)"
            Clock.schedule_once(lambda dt: self.show_error(err_msg))

    def create_hour_card(self, time_str, temp, code, is_day):
        card = BoxLayout(
            orientation = 'vertical',
            size_hint=(None, 1),
            width="65dp",
            padding = 5,
            spacing=2
        )
        icon_file = ("sun.png" if is_day==1 else "moon.png") if code in [0, 1] else ("cloud.png" if code in [2,3,45,48] else("groza.png" if code in [95,96,99] else "rain.png"))
        lbl_time = Label(text=time_str, font_size="12sp", color=(0.4,0.4,0.4,1))
        img_icon=Image(source=icon_file,size_hint=(1,1))
        lbl_temp = Label(text=f"{temp}°C", font_size="14sp", bold=True, color=(0.2,0.2,0.2,1))

        card.add_widget(lbl_time)
        card.add_widget(img_icon)
        card.add_widget(lbl_temp)

        return card

    def show_error(self, error_text="Неизвестная ошибка"):
        self.weather_canvas.stop_loader()
        self.status_label.font_size = "12sp"
        self.status_label.text =  f"Ошибка: {error_text}"
if __name__ == '__main__':
    WeatherApp().run()