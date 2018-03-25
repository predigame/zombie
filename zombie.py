# A Customizable Maze Game
# Editing this file is for 'expert' coders
from types import MethodType

# Window Constants
WIDTH = 31
HEIGHT = 19
TITLE = 'Zombie Madness'

# Statistics Constants
LEVEL_COMPLETE = 'Levels Completed'
PLAYER_KILLS = 'Player Kills'
RED_LAUNCH = 'Red Launched'
RED_KILLS = 'Red Kills'
BLUE_LAUNCH = 'Blue Launched'
BLUE_SAFE = 'Blue Safe'

# State Variables
current_level = None
stats = None

#
# Support functions
#
def invoke(plugins, function, default, **kwargs):
   """ call a plugin function or default to something else (if plugin doesn't have one we can call) """
   if function in plugins.__dict__:
      return plugins.__dict__[function](**kwargs)
   else:
      return globals()[default](**kwargs)

def monitor(a, cb):
   """ used by computer player (red and blue) to track progress and potentially replay movement """
   if a.action.startswith(IDLE):
      cb()
   if not a.action.startswith(DIE):
      callback(partial(monitor, a, cb), 0.75)

def arrive_destination(dest_sprite, target):
   """ when a blue actor arrives at their location (bottom right) """
   if target.tag == 'blue':
      target.destroy()
      current_level.blue_safe += 1
      current_level.player.wealth = 250
      stats.add(BLUE_SAFE, 1)

def default_blue_destination():
   """ the blue actor's destination image (bottom right) """
   return 'pigpen'

def red_attack(red, target):
   """ when red attacks """
   if target.tag == 'red':
      return
   if (target.tag == 'blue' or target.tag == 'player') and target.health > 0:
      if target.tag == 'blue':
         current_level.blue_killed += 1

      red.stop()
      red.act(ATTACK, 1)
      # This callback will cause the red to re-run another astar search
      callback(partial(red.act, IDLE_FRONT, FOREVER), 1)
      target.kill()
      stats.add(RED_KILLS, 1)

def red_murder(self):
    """ Override for Actor.kill. Called when player kills a red. Reward the player and tally the kill """
    if self.health > 0:
       current_level.red_killed += 1
       current_level.player.wealth = 100
       stats.add(PLAYER_KILLS, 1)
    Actor.kill(self)

def blue_murder(self):
    """ Override for Actor.kill. Calleed when a blue is killed (by either red or player). Punish player and tally the kill """
    if self.health > 0:
       callback(partial(current_level.create_red, self.pos), 0.5)
       current_level.blue_killed += 1
       current_level.player.wealth = -250
    Actor.kill(self)


class ZombieLevel(Level):
   """ Define a zombie level. """
   # read in the plugins file
   plugins = import_plugin('zombie_plugins.py')

   def __init__(self, targets=1, level=1, duration=0, time_remaining=30):
      self.targets = targets
      self.level = level
      self.time_remaining = time_remaining
      self.duration = duration
      self.blue_safe = 0
      self.blue_spawned = 0
      self.blue_killed = 0
      self.red_spawned = 0
      self.red_killed = 0
      self.destination = None
      self.player = None
      global current_level
      current_level = self

   def get_duration(self):
      return score(pos=LOWER_RIGHT)

   def create_blue(self):
      """ create a blue (friendly) actor """
      self.blue_spawned += 1
      atts = self.plugins.get_blue()
      blue = actor(atts[0], (1,1), tag='blue').speed(atts[1])
      self.destination.collides(blue, arrive_destination)
      if len(atts) == 3: blue.defend = atts[2]
      blue.old_kill = MethodType(blue.kill, blue)
      blue.kill = MethodType(blue_murder, blue)

      # callbacks - let reds know about this new blue actor
      for o in get('red'):
         o.collides(blue, red_attack)

      # movements - blues find a path to their destination
      cb = partial(track_astar, blue, ['destination'], pabort=0.1)
      callback(cb, 0.1)
      callback(partial(monitor, blue, cb), 0.75)
      stats.add(BLUE_LAUNCH, 1)

   def create_red(self, pos=(WIDTH-2,1)):
      """ create a red (hostile) actor """
      self.red_spawned += 1
      actor_name, speed = self.plugins.get_red()
      red = actor(actor_name, pos=pos, tag='red').speed(speed)
      red.old_kill = MethodType(red.kill, red)
      red.kill = MethodType(red_murder, red)

      # callbacks - reds attack blue and player
      for o in get('blue'):
         red.collides(o, red_attack)
      for o in get('player'):
         red.collides(o, red_attack)

      # movements - use astar algorithm to find and blue or player
      cb = partial(track_astar, red, ['blue', 'player'], pabort=0.1)
      callback(cb, 0.1)
      callback(partial(monitor, red, cb), 0.75)
      stats.add(RED_LAUNCH, 1)

   def setup(self):
      """ setup the level """

      # PLAYER
      self.player = actor(self.plugins.get_player(), (1, HEIGHT-2), tag='player', abortable=True)
      self.player.speed(5).keys(precondition=player_physics)

      # PLAYER Inventory (activated by F1 key)
      display('f1', 'inventory', self.player._inventory)

      # PLAYER Statistics (activated by F2 key)
      global stats
      stats = Statistics()
      load_state(stats, 'stats.pg')
      display('f2', 'stats', stats)

      # BLUE SAFETY DESTINATION
      self.destination = image(invoke(self.plugins, "blue_destination", "default_blue_destination"), pos=(WIDTH-2, HEIGHT-2), size=1, tag='destination')

      # KEYBOARD EVENTS - 'r' to restart
      keydown('r', reset)

      # USER DEFINED STUFF
      self.plugins.setup(self.player, self)

      # LOAD IN SAVED STATE
      load_state(self.player, 'player.pg')

      # CREATE FRIENDLIES - 1 per level
      for i in range(self.targets):
         self.create_blue()

      # CREATE HOSTILES - 1 per level
      for i in range(self.targets):
         self.create_red()

      # SCORE BOARD - Level Counter
      score(self.level, pos=UPPER_RIGHT, color=WHITE, method=VALUE, prefix='Level: ')

      # SCORE BOARD - ENERGY and WEALTH Counter
      def __update_status__(player):
        score("{:3d} | {:3d}".format(int(player.energy), int(player.wealth)), color=WHITE, pos=LOWER_LEFT, method=VALUE)
      callback(partial(__update_status__, self.player), wait=1, repeat=FOREVER)

   def completed(self):
      """ defines when a level is complete """

      if len(get('destination')) == 0:
         # blue destination destroyed
         text("DESTINATION DESTROYED! GAME OVER")
         gameover()
         save_state(stats, 'stats.pg')
      elif len(get('player')) == 0:
         # player dies
         text('GAME OVER')
         gameover()
         save_state(stats, 'stats.pg')
      elif len(get('blue')) == 0 and len(get('red')) == 0:
         # blues arrive safely and all zombies dead - next level
         self.player.energy = 50
         self.player.wealth = 250
         save_state(self.player, 'player.pg')
         stats.add(LEVEL_COMPLETE, 1)
         save_state(stats, 'stats.pg')
         return True
      else:
         # keep on playing
         return False

   def next(self):
       """ load the next level """
       if randint(1, 10) == 4:
          return WalkAcrossLevel(self.targets+1, level=self.level+1,
                                 duration=score(pos=LOWER_RIGHT))
       else:
          return ZombieLevel(self.targets+1, level=self.level+1,
                             duration=score(pos=LOWER_RIGHT))

class WalkAcrossLevel(Level):
   """ a randomly loaded surprise level """

   # read in the plugins file
   plugins = import_plugin('zombie_plugins.py')

   def __init__(self, targets=1, level=1, duration=0, time_remaining=30):
      self.level = level
      self.targets = targets
      self.duration = duration
      self.player = None
      global current_level
      current_level = self

   def setup(self):
      """ setup the level """

      # PLAYER
      self.player = actor(self.plugins.get_player(), (1, HEIGHT-2), tag='player', abortable=True)
      self.player.speed(5).keys(precondition=player_physics)

      # LOAD IN stats
      global stats
      stats = Statistics()
      load_state(stats, 'stats.pg')

      # SCORE BOARD
      score(self.level, pos=UPPER_RIGHT, color=BLACK, method=VALUE, prefix='Level: ')

      txt = text("TIME TO DIE!!")
      callback(txt.destroy, 4)

      # HOSTILE
      actor_name, speed = self.plugins.get_red()
      red = actor(actor_name, (WIDTH+15,5), tag='red', size=15).speed(8)
      red.collides(sprites(), red_attack)
      points = [(p, 5) for p in range(WIDTH+15, -15, -2)]
      red.move_to(*points, callback=red.destroy)

      keydown('r', reset)

   def completed(self):
      """ defines when a level is complete """
      if len(get('player')) == 0:
         # player dies
         text('GAME OVER')
         gameover()
      elif len(get('red')) == 0:
         # red walks completes walk across without kill player - player wins!
         self.player.wealth = 250
         stats.add(LEVEL_COMPLETE, 1)
         save_state(stats, 'stats.pg')
         return True

   def next(self):
       """ load the next level """
       return ZombieLevel(targets=self.targets+1, level=self.level+1,
                          duration=score(pos=LOWER_RIGHT))

# game entry point. start at level 1.
level(ZombieLevel(1))
