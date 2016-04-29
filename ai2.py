import random
import time
import multiprocessing
import math
import pygame
import logging 
import sys
import Queue
from sets import Set

# huristic weight
WH = 1
SPEED = 8
TIME = 0.001

# constants
(BUL,ENE,TIL,ME) = range(4)
(UP, RIGHT, DOWN, LEFT, NON) = range(5)
(TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)
(BASIC, FAST, POWER, ARMOR) = range(4)
(REC,DIR,SPD,ETY) = range(4)
CASTLE = pygame.Rect(12*16 - 16, 24*16 - 16, 32 + 16, 32 + 16)
SHL=3
TTY=1
UNMOVABLE = Set([TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_FROZE])
(TOPX, TOPY, BOTX, BOTY) = (0,0,416, 416)
(SHOOT,MOVE) = range(2)
skip_this = False

class ai_agent():
	mapinfo = []
	moves = [] # [(move, shoot)]
	walls = []
	wallsRect = []
	enemies = []
	enemiesRect = []
	bullets = []
	me = None

	def __init__(self):
		self.mapinfo = []

		logging.basicConfig(level=logging.INFO, format="%(levelname)s(%(lineno)d): %(funcName)s: %(message)s")

	# rect:					[left, top, width, height]
	# rect_type:			0:empty 1:brick 2:steel 3:water 4:grass 5:froze
	# castle_rect:			[12*16, 24*16, 32, 32]
	# mapinfo[0]: 			bullets [rect, direction, speed]]
	# mapinfo[1]: 			enemies [rect, direction, speed, type]]
	# enemy_type:			0:TYPE_BASIC 1:TYPE_FAST 2:TYPE_POWER 3:TYPE_ARMOR
	# mapinfo[2]: 			tile 	[rect, type] (empty don't be stored to mapinfo[2])
	# mapinfo[3]: 			player 	[rect, direction, speed, Is_shielded]]
	# shoot:				0:none 1:shoot
	# move_dir:				0:Up 1:Right 2:Down 3:Left 4:None

	# def Get_mapInfo:		fetch the map infomation
	# def Update_Strategy	Update your strategy

	# note: will perform shoot first then rotate

	"""
	generate a k list of aStar to direction
	@params 
		k int
		target pygame.Rect
	"""
	def aStar(self, target):
		log = logging.getLogger()
		# rect.move(offsetx, offsety), player w,h = [26, 26]
		closedList = {}
		openList = {} 
		end = None

		# index-> {"xxx,yyy": value}
		sKey = "%03d%03d" % (self.me[REC].x, self.me[REC].y)
		rect = self.me[REC]
		g = 0
		h = self.huristic(rect, target, SPEED)
		
		# g,h,f,parent,rect, direction
		(G,H,F,P,R,D)=range(6)
		openList[sKey] = [g, h, g+h, None, rect, self.me[DIR]]

		while len(openList) != 0:
			# get minimun cost OpenList object
			currentKey = reduce(lambda i,j: i if (openList[i][F]<openList[j][F]) else j, openList.keys())
			current = openList[currentKey]

			# GOAL TEST current
			if current[R].colliderect(target):
				log.info("g = %d" %current[G])
				end = current
				break

			if current[G] > 200:
				log.debug("Over limit")
				end = current
				break

			# put to closedList
			closedList[currentKey] = current
			del openList[currentKey]
			
			# neighbors path search
			neighbors = map(lambda d: [self.newPosition(current[R], current[D], d, SPEED), d], range(4))
			neighbors = filter(lambda x: self.passThroughCheck(x[0]) == 0, neighbors)

			# assemble to put to openList
			for neighbor in neighbors:
				nextRect = neighbor[0]
				nextDir = neighbor[1]
				sKey = "%03d%03d" % (nextRect.x, nextRect.y)
				g = current[G]+SPEED
				parent = current

				# repeated checking
				if sKey in openList:
					h = openList[sKey][H]
					if g <= openList[sKey][G]:
						openList[sKey] = [g, h, g+h, parent, nextRect, nextDir]

				elif sKey in closedList:
					pass
					#h = closedList[sKey][H]
					#if g < closedList[sKey][G]:
						#del closedList[sKey]
						#openList[sKey] = [g, h, g+h, parent, nextRect, nextDir]

				else:
					h = self.huristic(nextRect, target, SPEED)
					openList[sKey] = [g, h, g+h, parent, nextRect, nextDir]

		# perform from end
		if end is None:
			logging.info("a* search no route")
			return None

		current = end
		pathToGo = []

		while True:
			if current[P] is None:
				pathToGo += [current[D]] * max(1,int(SPEED/self.me[SPD]))
				break
			pathToGo += [current[D]] * max(1,int(SPEED/self.me[SPD]))
			current = current[P]

		return pathToGo

	"""
	@ret 
		pygame.Rect
	"""
	def getViewRect(self, rect, direction, width):
		global UP,DOWN,LEFT,RIGHT,TOPX,TOPY,BOTX,BOTY,REC

		half_width = max(1, width/2)

		if direction is UP:
			x = rect.centerx - half_width
			y = TOPY
			w = width
			h = abs(TOPY - rect.top) + half_width
		elif direction is RIGHT:
			x = rect.right - half_width
			y = rect.centery - half_width
			w = abs(BOTX - rect.right)
			h = width
		elif direction is DOWN:
			x = rect.centerx - half_width
			y = rect.bottom - half_width
			w = width
			h = abs(BOTY - rect.bottom)
		elif direction is LEFT:
			x = TOPX
			y = rect.centery - half_width
			w = abs(TOPX - rect.left) + half_width
			h = width

		return pygame.Rect(x,y,w,h)


	def updateInfo(self):
		# remove unmovable tile
		
		self.bullets = self.mapinfo[BUL]
		self.enemies = self.mapinfo[ENE]
		self.enemiesRect = map(lambda x: x[REC], self.enemies)
		self.walls = filter(lambda x: x[TTY] in UNMOVABLE, self.mapinfo[TIL])
		self.wallsRect = map(lambda x: x[REC], self.walls)
		
		# not consider shield as important info
		self.me = self.mapinfo[ME][0][0:3]
		
	"""
	Manhattan distance based
	@param
		s, t pygame.Rect, speed int
	@ret 
		int
	"""
	def huristic(self, s, t, speed):
		global WH
		h = self.diff(s,t) / SPEED
		return WH * h

	def diff(self, s, t):
		return (abs(s.x - t.x) + abs(s.y - t.y))

	def nearest(self, num, base):
		""" Round number to nearest divisible """
		return int(round(num / (base * 1.0)) * base)

	def fixPosition(self, target):
		new_x = self.nearest(target.left, 8) + 3
		new_y = self.nearest(target.top, 8) + 3

		if (abs(target.left - new_x) < 5):
			target.left = new_x

		if (abs(target.top - new_y) < 5):
			target.top = new_y

		return target

	"""
	@param
		origin: pygame.Rect
		direction int [0-3]
	@ret
		pygame.Rect
	"""
	def newPosition(self, origin, old_direction, new_direction, speed):
		copyOrigin = pygame.Rect(origin.x, origin.y, origin.w, origin.h)
		#if old_direction != new_direction:
		new_x = self.nearest(copyOrigin.left, speed)
		new_y = self.nearest(copyOrigin.top, speed)
		copyOrigin.left = new_x
		copyOrigin.top = new_y

		if new_direction == UP:
			copyOrigin.move_ip(0, -speed)
		elif new_direction == RIGHT:
			copyOrigin.move_ip(speed, 0)
		elif new_direction == DOWN:
			copyOrigin.move_ip(0, speed)
		elif new_direction == LEFT:
			copyOrigin.move_ip(-speed, 0)

		copyOrigin.w = copyOrigin.h = 32
		return copyOrigin

	"""
	@ ret:
		pygame.Rect
	"""
	def getNextEnemy(self):
		enemiesSet = self.getEnemiesNearCastle()
		if len(enemiesSet) == 0:
			enemiesSet = self.enemiesRect

		# nearest to player
		nearestEnemy = None
		nearest = sys.maxint
		for enemy in enemiesSet:
			l = self.diff(self.me[REC], enemy)
			nearest = min(l, nearest)
			nearestEnemy = enemy

		return nearestEnemy

	"""
	@ ret
		[pygame.Rect]
	"""
	def getEnemiesNearCastle(self):
		threshold = 12*16
		enemies = filter(lambda x: x.top>threshold, self.enemiesRect)
		return enemies

	"""
	@ ret
		index of pointed enemy
	"""
	def gunPointingEnemy(self):
		gunPoint = self.getViewRect(self.me[REC], self.me[DIR], 2)
		# check with enemy
		ei = gunPoint.collidelist(self.enemiesRect)
		if ei == -1:
			return ei

		# check with walls
		wi = gunPoint.collidelist(self.wallsRect)
		if wi == -1:
			return ei

		enemy = self.enemiesRect[ei]
		wall = self.wallsRect[wi]
		diff_enemy = abs(enemy.x - self.me[REC].x)+abs(enemy.y - self.me[REC].y)
		diff_wall = abs(wall.x - self.me[REC].x)+abs(wall.y - self.me[REC].y)

		if diff_wall < diff_enemy:
			return -1
		else:
			return ei


	def sameLineWithEnemy(self, nextShoot, nextMove):
		

		return (nextShoot, nextMove)

	def bulletCheck(self):
		# decide to dodge or shotback
		pass

	def assassinateCheck(self):
		# assasin 
		pass

	"""
	Tank will perform shoot first then move if actions given at same phare
	@ ret
		diff | False
	"""
	def willShootKing(self):
		# self.nextMove, self.me, self.walls
		global CASTLE,DIR,MOVE
		log = logging.getLogger()

		direction = self.me[DIR]

		viewRect = self.getViewRect(self.me[REC], self.me[DIR], 2)

		if viewRect.colliderect(CASTLE):
			log.info("Same line with King.")
			return True
		else:
			return False

	"""
	@ret: < 0 is unable to passthrough
		0: nothing
		-1: collide
		-2: out of range
	"""
	def passThroughCheck(self, rect):
		# wall collide
		ret = rect.collidelist(self.wallsRect)
		if ret != -1: 
			return -1
		
		# out of range
		if rect.top<TOPY or rect.top>BOTY-31 or rect.left<TOPX or rect.left>BOTX-31:
			return -2

		return 0
		
			
	def operations(self,p_mapinfo,c_control):
		log = logging.getLogger()

		pathToGo = []
		usePathToGo = False

		while True:
		#-----your ai operation,This code is a random strategy,please design your ai !!-----------------------

			time.sleep(TIME)
			self.Get_mapInfo(p_mapinfo)
			self.updateInfo()
		
		#-------------------------------
			nextDirection = NON
			nextShoot = 0
			# nextMove
			if skip_this:
				logging.info("Blocking")
				continue 

			# direction decision
			if not usePathToGo:
				# find an enemy
				target = self.getNextEnemy()
				if target is not None:
					log.info("next target: (%d,%d)"%(target.x/16, target.y/16))
					pathToGo = self.aStar(target)
		
			if pathToGo is None or len(pathToGo) is 0:
				usePathToGo = False
			else:
				nextDirection = pathToGo[0]
				usePathToGo = True

			(patchShoot, patchDirection) = self.sameLineWithEnemy(nextShoot, nextDirection)
			
			# shoot decision
			pointEnemyIndex = self.gunPointingEnemy()
			if pointEnemyIndex != -1: 
				logging.info("Enemy In Front Me")
				if not self.willShootKing():
					logging.info("No King In Front Me")
					nextShoot = 1
				else:
					logging.info("King maybe In Front Me")
					pointEnemy = self.enemiesRect[pointEnemyIndex]
					enemyDiff  = abs(self.me[REC].x - pointEnemy.x) + abs(self.me[REC].y - pointEnemy.y)
					kingDiff = abs(self.me[REC].x - CASTLE.x) + abs(self.me[REC].y - CASTLE.y)
					if enemyDiff < kingDiff:
						logging.info("No King In Front Me")
						nextShoot = 1

			#log.info("(shoot=%d, nextmove=%d)" % (nextShoot,nextDirection))
			if self.Update_Strategy(c_control, nextShoot, nextDirection, 0):
				if usePathToGo:
					del pathToGo[0]


	def Get_mapInfo(self,p_mapinfo):
		if p_mapinfo.empty()!=True:
			try:
				self.mapinfo = p_mapinfo.get(False)
				skip_this=False
			except Queue.Empty:
				skip_this=True

	def Update_Strategy(self,c_control,shoot,move_dir,keep_action=1):
		if c_control.empty() == True:
			c_control.put([shoot,move_dir,keep_action])
			return True
		else: 
			return False
