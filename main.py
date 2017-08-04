#!/usr/local/bin/python
print ("Content-Type: text/html\n\n")

__version__ = '1.0.0'

import kivy
kivy.require("1.8.0")

from random import randint, choice
import sys

from kivy.properties import NumericProperty, ReferenceListProperty, BooleanProperty, ObjectProperty, ListProperty
from kivy.uix.image import Image
from kivy.vector import Vector
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore
from time import sleep
from kivy.utils import platform

if platform() == "android":
    from jnius import cast
    from jnius import autoclass

class Background(Widget):
    image_one = ObjectProperty(Image())
    image_two = ObjectProperty(Image())

    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    def update(self):
        self.image_one.pos = Vector(*self.velocity) + self.image_one.pos
        self.image_two.pos = Vector(*self.velocity) + self.image_two.pos

        if self.image_one.right <= 0:
            self.image_one.pos = (1920, 0)
        if self.image_two.right <= 0:
            self.image_two.pos = (1920, 0)

    def update_position(self):
        self.image_one.pos = (0, 0)
        self.image_two.pos = (1920, 0)

class Mcnay(Widget):
    bird_image = ObjectProperty(Image())

    jump_time = NumericProperty(0.3)
    jump_height = NumericProperty(70)

    time_jumped = NumericProperty(0)

    jumping = BooleanProperty(False)

    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    normal_velocity_x = NumericProperty(0)
    normal_velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    normal_velocity = ReferenceListProperty(normal_velocity_x, normal_velocity_y)

    def __init__(self, **kwargs):
        super(Mcnay, self).__init__(**kwargs)
        if Config.getdefault('input', 'keyboard', False):
            self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
            self._keyboard.bind(on_key_down=self._on_keyboard_down)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def switch_to_normal(self, dt):
        self.bird_image.source = "images/flappyup.png"
        Clock.schedule_once(self.stop_jumping, self.jump_time  * (4.0 / 5.0))

    def stop_jumping(self, dt):
        self.jumping = False
        self.bird_image.source = "images/flappy.png"
        self.velocity_y = self.normal_velocity_y

    def on_touch_down(self, touch):
        self.jumping = True
        self.bird_image.source = "images/flappynormal.png"
        self.velocity_y = self.jump_height / (self.jump_time * 60.0)
        Clock.unschedule(self.stop_jumping)
        Clock.schedule_once(self.switch_to_normal, self.jump_time  / 5.0)

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self.on_touch_down(None)

    def update(self):
        self.pos = Vector(*self.velocity) + self.pos
        # Если рыба упала на грунт - то ползёт по нему
        if self.pos[1] <= 104:
            Clock.unschedule(self.stop_jumping)
            self.bird_image.source = "images/flappynormal.png"
            self.pos = (self.pos[0], 104)

class Obstacle(Widget):
    obstacle_image = ObjectProperty(Image())
    gap_top = NumericProperty(0)																					# Позиция отсчитывается снизу

    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    marked = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Obstacle, self).__init__(**kwargs)																	# Можно убрать без негативных последствий

    def update_position(self):
        self.gap_top = randint(104, self.height)													# Задаётся случайное расположение нового проёма в трубах

    def update(self):
        self.pos = Vector(*self.velocity) + self.pos																# Здесь задаётся только перемещение труб

class Skillball(Widget):
    skillball_image = ObjectProperty(Image())
    gap_top = NumericProperty(0)																					# Позиция отсчитывается снизу

    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)

    marked = BooleanProperty(False)
    marked2 = BooleanProperty(False)

    def __init__(self, **kwargs):
        super(Skillball, self).__init__(**kwargs)																	# Можно убрать без негативных последствий

    def update_position(self):
        self.gap_top = randint(104, self.height)													# Задаётся случайное расположение нового проёма в трубах

    def update(self):
        self.pos = Vector(*self.velocity) + self.pos																# Здесь задаётся только перемещение труб

class NewGamePopup(ModalView):
    def share(self):
        if platform() == 'android':
            record = 'Мой рекорд в Against the Stream: ' + str(StreamGame.store.get('tito')['inpud']) + ' баллов.'

            PythonActivity = autoclass('org.renpy.android.PythonActivity') #request the Kivy activity instance
            Intent = autoclass('android.content.Intent') # get the Android Intend class

            String = autoclass('java.lang.String') # get the Java object

            intent = Intent() # create a new Android Intent
            intent.setAction(Intent.ACTION_SEND) #set the action

            # to send a message, it need to be a Java char array. So we use the cast to convert and Java String to a Java Char array
            intent.putExtra(Intent.EXTRA_SUBJECT, cast('java.lang.CharSequence', String('Мой рекорд в Against the Stream'.decode('utf-8'))))
            intent.putExtra(Intent.EXTRA_TEXT, cast('java.lang.CharSequence', String(record.decode('utf-8'))))

            intent.setType('text/plain') #text message

            currentActivity = cast('android.app.Activity', PythonActivity.mActivity)
            currentActivity.startActivity(intent) # show the intent in the game activity

class StreamGame(Widget):
    mcnay = ObjectProperty(Mcnay())
    background = ObjectProperty(Background())
    skillballs = ListProperty([])
    obstacles = ListProperty([])
    score = NumericProperty(0)
    obstacle_sound = SoundLoader.load('audios/crash.mp3')
    skill_sound = SoundLoader.load('audios/skill.mp3')
    store = JsonStore('hello.json')

    def __init__(self, **kwargs):
        super(StreamGame, self).__init__(**kwargs)
        self.mcnay.normal_velocity = [0, -6]
        self.mcnay.velocity = self.mcnay.normal_velocity
        self.background.velocity = [-4, 0]
        self.bind(size=self.size_callback)

    def remove_skillball(self):
        self.remove_widget(self.skillballs[0])																		# Удаляем только первый объект из списка труб
        self.skillballs = self.skillballs[1:]																			# Обновляем переменную со всеми трубами - присваиваем ей новый список без первой трубы

    def remove_obstacle(self):
        self.remove_widget(self.obstacles[0])																		# Удаляем только первый объект из списка труб
        self.obstacles = self.obstacles[1:]																			# Обновляем переменную со всеми трубами - присваиваем ей новый список без первой трубы

    def new_skillball(self, remove=True):
        if remove:
            self.remove_skillball()
        new_skillball = Skillball()
        new_skillball.skillball_image.source = "images/score_" + choice(["red", "blue", "green"]) +".png"
        new_skillball.height = self.height																			# Высота трубы задаётся по высоте экрана
        new_skillball.x = self.width																					# Ширина задаётся из сопровождающего файла .kv - то есть 30 пикселей
        new_skillball.update_position()																				# Вызываем метод для создания случайной позиции проёма в трубе
        new_skillball.velocity = [-6, 0]																				# Задаём скорость трубе
        self.add_widget(new_skillball)																				# Выводим трубу на экран
        self.skillballs = self.skillballs + [new_skillball]															# Добавляем в общий список с трубами созданную только что трубу

    def new_obstacle(self, remove=True):
        if remove:
            self.remove_obstacle()
        new_obstacle = Obstacle()
        new_obstacle.obstacle_image.source = "images/obstacle.png"
        new_obstacle.height = self.height																			# Высота трубы задаётся по высоте экрана
        new_obstacle.x = self.width																					# Ширина задаётся из сопровождающего файла .kv - то есть 30 пикселей
        new_obstacle.update_position()																				# Вызываем метод для создания случайной позиции проёма в трубе
        new_obstacle.velocity = [-8, 0]																				# Задаём скорость трубе
        self.add_widget(new_obstacle)																				# Выводим трубу на экран
        self.obstacles = self.obstacles + [new_obstacle]															# Добавляем в общий список с трубами созданную только что трубу

    def size_callback(self, instance, value):
        for skillball in self.skillballs:
            skillball.height = value[1]
            skillball.update_position()
        for obstacle in self.obstacles:
            obstacle.height = value[1]
            obstacle.update_position()
        self.background.size = value
        self.background.update_position()

    def reset(self, dt):
        sleep(1)
        self.score = 0
        self.mcnay.pos = (self.parent.center)
        for obstacle in self.obstacles:
            self.remove_widget(obstacle)
            self.obstacles = self.obstacles[1:]
        for skillball in self.skillballs:
            self.remove_widget(skillball)
            self.skillballs = self.skillballs[1:]
        Clock.unschedule(self.update)
        Clock.schedule_interval(self.update, 1.0/90.0)
        Clock.schedule_once(self.mcnay.stop_jumping, self.mcnay.jump_time  * (4.0 / 5.0))
        self.background.update_position()

    def update(self, dt):
        self.mcnay.update()
        self.background.update()

        # Циклично создаём планктон. Удаляем то, что ушло за левый край экрана
        for skillball in self.skillballs:
            skillball.update()
            # Как только планктон пройден рыбой - создаём ещё один впереди
            if skillball.x < self.mcnay.x + self.mcnay.x/2 and not skillball.marked:
                skillball.marked = True
                self.new_skillball(remove=False)
        if len(self.skillballs) == 0:																				# Если список с трубами пуст - добавляем в него одну трубу
            self.new_skillball(remove=False)
        elif self.skillballs[0].x < 0:																				# Иначе, если первая труба в списке вышла за левый край - вызываем метод её удаления
            self.remove_skillball()

        # Циклично создавать трубы. Удалять трубы, которые выходят за левый край экрана.
        for obstacle in self.obstacles:
            obstacle.update()																						# Вызываем метод для передвижения трубы
            if obstacle.x < self.mcnay.x and not obstacle.marked:													# Как только труба пройдена птицей - прибавляем одно очко и создаём ещё одну трубу впереди
                obstacle.marked = True
                self.new_obstacle(remove=False)
        if len(self.obstacles) == 0:																				# Если список с трубами пуст - добавляем в него одну трубу
            self.new_obstacle(remove=False)
        elif self.obstacles[0].x < 0:																				# Иначе, если первая труба в списке вышла за левый край - вызываем метод её удаления
            self.remove_obstacle()
        
		# Задаём алгоритм действий при столкновении рыбы с амёбой
        for obstacle in self.obstacles:
            if self.mcnay.collide_widget(Widget(pos=(obstacle.x - 5, obstacle.gap_top + 30), size=(obstacle.width, 10))):
                # Если рыба столкнулась с амёбой - выход из приложения
                obstacle.obstacle_image.source = "images/obstacle_shocked.png"
                Clock.unschedule(self.update)
                Clock.unschedule(self.mcnay.stop_jumping)
                self.obstacle_sound.play()
                if self.score > self.store.get('tito')['inpud']:
                    self.store.put('tito', inpud=self.score)

                # Имеет смысл выделить этот код в отдельную функцию
                popup = NewGamePopup()
                victory_label = Label(text="[color=#000][b]Мой результат в игре\nAgainst the Stream[/b]\nДостигнуто: " + str(self.score) + "\nРекорд: " + str(self.store.get('tito')['inpud']) + "\n\n\n[/color]", markup = True, font_size=30, pos_hint={'top':0.1})
                popup.add_widget(victory_label)
                popup.bind(on_dismiss=self.reset)
                popup.open()

        for skillball in self.skillballs:
            if self.mcnay.collide_widget(Widget(pos=(skillball.x, skillball.gap_top + 20), size=(skillball.width, 14))) and not skillball.marked2:
                skillball.marked2 = True
                self.skill_sound.play()
                # Если рыба заглотила красный планктон - плюс один балл
                if skillball.skillball_image.source == "images/score_red.png":
                    self.score += 1
                # Если проглочен планктон другого цвета - минус один балл
                else:
                    self.score -= 1
                skillball.skillball_image.source = "images/none.png"

class FlappyBirdApp(App):

    def build(self):
        game = StreamGame()
        # Частота обновлений кадров в секунду
        Clock.schedule_interval(game.update, 1.0/90.0)
        return game

    def on_pause(self):
        return True

if __name__ == "__main__":
    FlappyBirdApp().run()