import random
from PIL import Image, ImageDraw, ImageFont
import os
import shutil
from multiprocessing import Process

STARTING_HUNGER=.5
EXPENSE = STARTING_HUNGER/(60.0*3.0) #starve in one half hour
EATING = EXPENSE*20 #eating adds 10
RADIUS = 50.0
MOVEMENT = 3.0 #SCOTLAND FOREVER
SEARCH = 6.0
PERSIST = (60*60*2)
INTERVAL = 10
SIM_TIME = 60*60*8

DESC = "%f-%f-%f-%d-%d-%d_"%(STARTING_HUNGER, EXPENSE, EATING,
							RADIUS, MOVEMENT, PERSIST)

graves = []

death_log = open("deaths.csv", "w")
death_log.write(",".join(["Player","Dist to target", "Dist travelled"])+"\n")

# font = ImageFont.load("arial.pil")

def bmp_to_png(fr, to):
	os.system('"C:\Program Files (x86)\IrfanView\i_view32.exe" '+fr+' /convert='+to)#need to install irfanview for this
	os.remove(fr)
	shutil.move(to,"./frames/"+to)
	return

def rand_rad(rad):
	x = random.uniform(-rad,rad)
	y = (rad**2.0-x**2.0)**.5
	
	y = random.uniform(-y,y)
	
	# flip = random.randint(0, 1)
	# if flip == 1:
		# y = y*-1.0
	return x,y

def draw_map(m, label = None, ts = ""):
	global graves
	global font
	im = Image.new("RGB", (1400, 1400), "#009933")
	draw = ImageDraw.Draw(im)
	
	# draw.text((10,10), ts, fill = "white", font=font)
	
	for t in m.targets:
		x,y = (int(t.x), int(t.y))
		draw.ellipse((x-10, y-10, x+10, y+10), fill = '#33CC33')
	
	for p in graves:
		x,y = (int(p.x)-1, int(p.y)-1)
		draw.ellipse((x-2, y-2, x+2, y+2), fill = 'black')
		
	for p in m.players:
		x,y = (int(p.loc.x)-1, int(p.loc.y)-1)
		rad = int(p.hunger*5.0)+1
		draw.ellipse((x-rad, y-rad, x+rad, y+rad), fill = 'blue')
		
	for l in m.loot:
		x,y = (int(l.x)-1, int(l.y)-1)
		draw.ellipse((x-3, y-3, x+3, y+3), fill = '#663300')
		
	if label:
		fn = ""+DESC+label+".bmp"
		cvt = ""+DESC+label+".gif"
		im.save(open(fn, "w"), 'bmp')
		p = Process(target=bmp_to_png, args=(fn, cvt))
		p.start()
	else:
		im.show()
	

class location(object):
	def __init__(self, x, y):
		self.x = x
		self.y = y
		
	def __sub__(self, other):
		return ((self.x-other.x)**2+(self.y-other.y)**2)**.5
		
	def __str__(self):
		return "X: "+str(self.x)+", Y: "+str(self.y)
		
	def riserun(self, other):
		return (other.y-self.y), (other.x-self.x)
		
	def slope(self, other):
		rr = self.riserun(other)
		return rr[0]/rr[1]
		
class loot(location):
	def __init__(self, x, y, map):
		self.map = map
		self.life = PERSIST
		location.__init__(self,x,y)
	def tick(self):
		self.life -= 1
		if self.life <= 0:
			self.map.despawn(self)
		
class game_map(object):
	def __init__(self, x_lim, y_lim):
		self.x_lim = x_lim
		self.y_lim = y_lim
		self.loot = []
		self.players = []
		self.targets = [location(340, 230),
						location(480, 520),
						location(380, 640),
						location(590, 510),
						location(300, 740),
						location(260, 1000),
						location(180, 1310),
						location(360, 1290),
						location(450, 1290),
						location(570, 1280),
						location(610, 1210),
						location(650, 1180),
						location(670, 1280),
						location(1030, 1320),
						location(1190, 1180),
						location(1340, 900),
						location(1230, 570),
						location(1110, 300),
						location(1210, 270),
						location(1390, 200),
						location(1170, 90),
						location(780, 260),
						location(520, 670),
						location(610, 760),
						location(700, 760),
						location(950, 650),
						location(1070, 730),
						location(440, 1070),
						location(440, 890),
						location(470, 850),
						location(580, 1060),
						location(1010, 1000),
						location(760, 1020)]
		
	def random(self):
		x = random.uniform(0,self.x_lim)
		y = random.uniform(0,self.y_lim)
		return location(x,y)
		
	def isin(self, loc):
		return loc.x<=self.x_lim and \
				loc.x>=0 and \
				loc.y>=0 and \
				loc.y<=self.y_lim
		
	def spawn_one_loot(self, cause = None):
		rad = rand_rad(100.0)
		town = random.choice(self.targets)
		new = location(town.x+rad[0], town.y+rad[1])
		while cause and cause.loc-new < RADIUS and self.isin(new):
			rad = rand_rad(100.0)
			town = random.choice(self.targets)
			new = location(town.x+rad[0], town.y+rad[1])
		self.loot += [loot(new.x, new.y, self)]
		
	def spawn_loot(self, ct):
		for _ in xrange(ct):
			self.spawn_one_loot()
			
	def spawn_one_player(self):
		new = self.random()
		flip = random.randint(0, 1)
		if flip == 1:
			new.x = self.x_lim
		else:
			new.y = self.y_lim
		self.players += [player(self, start = new)]
		
	def spawn_players(self, ct):
		for _ in xrange(ct):
			self.spawn_one_player()
			
	def players_within(self, loc, dist):
		ps = []
		for p in self.players:
			if p.loc-loc < dist:
				ps += [p]
		return ps
		
	def loot_within(self, loc, dist):
		ls = []
		for l in self.loot:
			if l-loc < dist:
				ls += [l]
		return ls
		
	def tick(self):
		# print "---TICK---"
		for p in self.players:
			p.tick()
		for l in self.loot:
			l.tick()
		
	def kill(self, player):
		global graves
		global death_log
		graves += [player.loc]
		death_log.write(",".join([str(id(player)),str(player.loc-player.target), str(player.loc-player.start)])+"\n")
		self.players.remove(player)
		self.spawn_one_player()
		
	def despawn(self, l):
		self.loot.remove(l)
		self.spawn_one_loot()
		
class player(object):
	def __init__(self, map, start = location(0,0)):
		self.loc=start
		self.start = location(start.x,start.y)
		self.hunger=STARTING_HUNGER
		self.inv = []
		self.capacity = 5
		self.map = map
		self.target = random.choice(map.targets)
		
	def isfull(self):
		if self.hunger+EATING > 1.0:
			return True
		return False
		
	def move(self, at):
		if self.loc-self.target < MOVEMENT:
			self.target = random.choice(self.map.targets)
		ratio = MOVEMENT / (self.loc-at)
		rr = self.loc.riserun(at)
		self.loc.y += rr[0]*ratio
		self.loc.x += rr[1]*ratio
		self.loc.y += random.uniform(-MOVEMENT,MOVEMENT)
		self.loc.x += random.uniform(-MOVEMENT,MOVEMENT)
		# print id(self), self.loc
	
	def loot_area(self):
		loot = self.map.loot_within(self.loc, SEARCH)
		if loot:
			while loot and len(self.inv) < self.capacity:
				self.inv.append(loot[0])
				self.map.loot.remove(loot[0])
				self.map.spawn_one_loot(self)
				loot = self.map.loot_within(self.loc, SEARCH)
				print id(self), "MINE"
				
	def eat(self):
		while self.inv and not self.isfull():
			self.inv.pop()
			self.hunger += EATING
			print id(self), "NOM"
		
	def tick(self):
		if self.hunger < 0.0:
			print id(self), "DEAD"
			self.map.kill(self)
		self.hunger -= EXPENSE
		self.move(self.target)
		self.loot_area()
		self.eat()
	
def main():
	global graves
	m = game_map(1400, 1400)
	m.spawn_players(30)
	m.spawn_loot(1000)
	
	
	for _ in xrange(SIM_TIME):
		try:
			m.tick()
			if _ % (INTERVAL) == 0:
				label = "%010d" % _
				draw_map(m, label)
		except Exception as e:
			print e
			break
		
	# f = open(
	
	return
	
if __name__ == '__main__':
	main()
