# A Place for gamer customizations
# This file is called by zombie.py

def setup(player, level):
   """ setup is called for every level. this is a place to add new things. """

   # create a grass background image (using backgrounds/grass.png)
   background('grass')

   # create a randomly generated maze (using images/stone.png images)
   maze(callback=partial(image, 'stone'))

   # redirect the player movement controls to w-a-s-d
   player.keys(right = 'd', left = 'a', up = 'w', down = 's')

   # load in all the weapsons defined in the weapons.py file
   weapons = import_plugin('weapons.py')

   # define player capabilities using the abstraction of a player "taking" a given capability
   # all capabilities are optional, call relates to the keyboard event callback
   player.take(weapons.EnergyDrink())
   player.take(weapons.Punch(call='1'))
   player.take(weapons.FlameThrower(call='2'))
   player.take(weapons.Grenade(call='3', distance=6, radius=10))
   player.take(weapons.MustardGas(call='4', distance=10, radius=20))
   player.take(weapons.AirGun(call='space'))
   player.take(weapons.MachineGun(call='5', distance=15, repeat=3))
   player.take(weapons.Landmine(call='6', delay=1))
   player.take(weapons.C4(call='7', detonate='8', distance=8, radius=10))
   player.take(weapons.NuclearBomb(call='n'))
   player.take(weapons.WallBuster())

   # dynamically build walls with the arrow keys
   #wall = partial(image, 'stone')
   #player.take(WallBuilder(left='left', right='right', front='up', back='down', wall=wall))

   # reward the player with an enery boost - 5% probability of displaying
   def drink(soda, player):
      soda.destroy()
      player.energy = 10
   fill(partial(image,'drink', size=1.0), 0.05, player, drink)

   # reward the player with a wealth boost - 25% probability of displaying
   def claim(coin, player):
      coin.destroy()
      player.wealth = 5
   fill(partial(image,'money', size=1.0), 0.25, player, claim)
#end of setup()

def get_blue():
   """ create a blue (friendly) actor """
   # return name of actor, grazing speed, self defense
   return 'Boar', 2

def get_red():
   """ create a red (hostile) actor """
   # return name of actor, movement speed (maximum speed 10)
   zombies = ['Zombie-1','Zombie-2','Zombie-3']
   return choice(zombies), randint(1,4)

def get_player():
   # name of player sprite (must exist in actors/ directory)
   return 'Soldier-1'
