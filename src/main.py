
from kivy.config import Config
Config.set('graphics','resizable',0)
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, BooleanProperty, NumericProperty
from kivy.event import EventDispatcher
from kivy.core.window import Window
from kivy.logger import Logger
import random

class RetryScreen(Screen): pass

class GameScreen(Screen): pass

class SplashScreen(Screen): pass

class Ball(Widget):

    velocity = NumericProperty(0)

    def up(self):
        self.velocity = 9

    def update(self, *args):
        self.velocity -= 0.5
        self.y += self.velocity

class Bar(Widget): pass

class Obstacle(Widget):
    
    top_bar = ObjectProperty(None)
    bottom_bar = ObjectProperty(None)
    opening_y = NumericProperty(0)
    counted = BooleanProperty(False)

class BounceGame(Widget):
    
    ball = ObjectProperty(None)
    playing = BooleanProperty(False)
    points = NumericProperty(0)
    obstacles = []

    def stop(self):
        self.playing = False
        self.end_game()

    def bounce(self, *args):
        if self.parent.manager.current == self.parent.name:
            self.playing = True
            self.ball.up()

    def update(self, *args):
        if self.playing:
            self.ball.update()
            for obstacle in self.obstacles:
                obstacle.x -= 4
                if obstacle.x < -100:
                    self.obstacles.remove(obstacle)
                    self.remove_widget(obstacle)
                if not obstacle.counted and obstacle.center_x < self.ball.x:
                    self.points += 1
                    obstacle.counted = True
            if self.check_collision():
                self.end_game()
                
    def reset(self):
        self.ball.pos = self.width / 4, self.height / 3
        for obstacle in self.obstacles:
            self.remove_widget(obstacle)
        self.obstacles = []
        self.points = 0

    def new_obstacle(self, *args):
        if self.playing:
            obstacle = Obstacle(pos=(1000, 0), opening_y = random.randint(50, self.height - 350))
            self.obstacles.append(obstacle)
            self.add_widget(obstacle)

    def check_collision(self):
        ground = self.ball.y < 3
        obstaclel = [self.ball.collide_widget(ob.top_bar) or self.ball.collide_widget(ob.bottom_bar) for ob in self.obstacles]
        obstacle = True in obstaclel
        return ground or obstacle

    def on_game_over(self):
        pass

    def end_game(self):
        self.dispatch('on_game_over')

class BounceApp(App):

    points = NumericProperty(0)
    highscore = NumericProperty(0)
    highscore_file = ObjectProperty(None)

    def on_game_over(self, *args):
        self.game.playing = False
        self.highscore = max(self.points, self.highscore)
        self.screenmanager.current = 'retry'

    def on_retry(self, *args):
        self.game.reset()
        self.screenmanager.current = 'game'

    def on_open(self, *args):
        self.highscore_file = open('data/highscore', 'r+')
        self.highscore_file.seek(0)
        self.highscore = int(self.highscore_file.read())

    def on_close(self, *args):
        self.highscore_file.seek(0)
        self.highscore_file.write(str(self.highscore))
        self.highscore_file.close()

    def update(self, *args):
        self.game.ball.update()

    def update_points(self, *args):
        self.points = self.game.points

    def build(self):
        self.bind(on_start=self.on_open) # opens highscore file
        self.bind(on_stop=self.on_close) # writes to highscore file
        self.screenmanager = ScreenManager(transition=FadeTransition())
        self.screenmanager.add_widget(SplashScreen(name='splash'))        
        self.screenmanager.add_widget(GameScreen(name='game'))
        self.screenmanager.add_widget(RetryScreen(name='retry'))
        self.game = self.screenmanager.get_screen('game').ids['game']
        self.game.register_event_type('on_game_over')
        self.game.bind(points=self.update_points) # keep app.points property updated
        self.game.bind(on_game_over=self.on_game_over)
        self.keyboard = Window.request_keyboard(None, self, 'text')
        self.keyboard.bind(on_key_down=self.game.bounce)
        Clock.schedule_interval(self.game.update, 1/30)
        Clock.schedule_interval(self.game.new_obstacle, 2)
        return self.screenmanager

if __name__ == '__main__':
    app = BounceApp()
    try:
        app.run()
    except BaseException as e:
        Logger.critical('Toplevel: The application has crashed for an unknown reason, attempting to close gracefully')
        app.dispatch('on_stop') # this is so the highscore is saved
