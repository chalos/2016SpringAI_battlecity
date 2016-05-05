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
TIME = 0.01

max_g = 600

# constants
(BUL,ENE,TIL,ME) = range(4)
(UP, RIGHT, DOWN, LEFT, NON) = range(5)
(TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)
(BASIC, FAST, POWER, ARMOR) = range(4)
(REC,DIR,SPD,ETY) = range(4)
CASTLE = pygame.Rect(12*16 - 16, 24*16 - 16, 32 + 16, 32 + 16)
TOP_GEN = pygame.Rect(416/2, 0, 8, 8)
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
	bulletsRect = []
	bulletsView = []
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
	@dep:
		SPEED
	@params 
		k int
		target pygame.Rect
	"""
	def aStar(self, target):
		log = logging.getLogger()
		target = pygame.Rect(target.x, target.y, target.w/2, target.h/2)
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
		openList[sKey] = [g, h, g+h, None, rect, None]

		while len(openList) != 0:
			# get minimun cost OpenList object
			currentKey = reduce(lambda i,j: i if (openList[i][F]<openList[j][F]) else j, openList.keys())
			current = openList[currentKey]

			# GOAL TEST current
			if current[R].colliderect(target):
				end = current
				break

			if current[G] > max_g:
				log.info("Over limit")
				end = current
				break

			# put to closedList
			closedList[currentKey] = current
			del openList[currentKey]
			
			# neighbors path search 
			# newPosition(originRect, old_direction, new_direction, speed)
			neighbors = map(lambda new_d: [self.newPosition(current[R], current[D], new_d, SPEED), new_d], range(4))
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
						# g,h,f,parent,rect, direction
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

		debug_pathToGo = ""
		debugPath = ["U","R","D","L"]
		while True:
			if current[P] is None:
				break
			# append (direction, checkPoint?)
			pathToGo += [(current[D],None)]*(max(1,int(SPEED/self.me[SPD]))-1) + [(current[D],current[P][R])]
			debug_pathToGo += debugPath[current[D]] + "<-"
			current = current[P]

		#logging.info(debug_pathToGo)
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
			h = abs(TOPY - rect.top) #+ half_width
		elif direction is RIGHT:
			x = rect.right #- half_width
			y = rect.centery - half_width
			w = abs(BOTX - rect.right)
			h = width
		elif direction is DOWN:
			x = rect.centerx - half_width
			y = rect.bottom #- half_width
			w = width
			h = abs(BOTY - rect.bottom)
		elif direction is LEFT:
			x = TOPX
			y = rect.centery - half_width
			w = abs(TOPX - rect.left) #+ half_width
			h = width

		return pygame.Rect(x,y,w,h)


	def updateInfo(self):
		# remove unmovable tile
		
		self.bullets = self.mapinfo[BUL]
		self.bulletsRect = map(lambda x: x[REC], self.bullets)
		self.bulletsView = map(lambda x: self.getBulletView(x), self.bullets)
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

		if new_direction == UP:
			copyOrigin.move_ip(0, -speed)
		elif new_direction == RIGHT:
			copyOrigin.move_ip(speed, 0)
		elif new_direction == DOWN:
			copyOrigin.move_ip(0, speed)
		elif new_direction == LEFT:
			copyOrigin.move_ip(-speed, 0)

		copyOrigin.w = copyOrigin.h = 26

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
		threshold = 416/3*2
		enemies = filter(lambda enemy: enemy.top>threshold, self.enemiesRect)
		return enemies

	"""
	@ ret
		index of pointed enemy
	"""
	def gunPointingEnemy(self, dir_offset=0):
		gunPoint = self.getViewRect(self.me[REC], (self.me[DIR]+dir_offset)%4, 3)
		# check with enemy
		ei = gunPoint.collidelist(self.enemiesRect)
		
		if ei == -1:
			return ei

		# check with walls
		colli_walls_index = gunPoint.collidelistall(self.wallsRect) # list of colli_walls index
		colli_walls_index = filter(lambda wi: self.walls[wi][TTY] in (TILE_STEEL, TILE_FROZE), colli_walls_index)
		if len(colli_walls_index) == 0:	
			return ei

		# nearest walls
		diff_colli_walls = map(lambda wi: self.diff(self.wallsRect[wi], self.me[REC]), colli_walls_index)	
		wi = 0
		diff_wall = sys.maxint
		for i in range(len(diff_colli_walls)):
			if diff_colli_walls[i] < diff_wall:
				wi = i
				diff_wall = diff_colli_walls[i]

		enemy = self.enemiesRect[ei]
		diff_enemy = self.diff(enemy, self.me[REC])

		if diff_wall < diff_enemy:
			return -1
		if diff_enemy > 100:
			return -1
		else:
			return ei
	
	def getBulletView(self, bullet):
		if bullet[DIR] in (UP,DOWN):
			w = bullet[REC].w 
		else:
			w = bullet[REC].h 
		return self.getViewRect(bullet[REC], bullet[DIR], w)

	def performActions(self, bi):
		bulletDir = (self.bullets[bi][DIR]+2)%4
		gunView = self.getViewRect(self.me[REC], bulletDir, 3)
		bulletView = self.getBulletView(self.bullets[bi])
		if gunView.colliderect(bulletView):
			# collide the killer bullet with bullet
			return [[0,bulletDir],[1, NON]]
		# not able to collide with bullet, dodge it
		diff_bullet = self.diff(self.me[REC], self.bulletsRect[bi])
		if diff_bullet > 100:
			return []
		if self.bullets[bi][DIR] in (UP, DOWN):
			center_diff = self.me[REC].centerx - self.bulletsRect[bi].centerx
			if center_diff < 0:
				# player at left, dodge left
				return [[0,LEFT]] * int(abs(center_diff/2))
			else:
				# player at right, dodge right
				return [[0,RIGHT]] * int(abs(center_diff/2))
		else: #(LEFT,RIGHT)
			center_diff = self.me[REC].centery - self.bulletsRect[bi].centery
			if center_diff < 0:
				# player at top, dodge up
				return [[0,UP]] * int(abs(center_diff/2))
			else:
				# player at bot, dodge down
				return [[0,DOWN]] * int(abs(center_diff/2))
		return []

	"""
	Bullet check on direction
	@ ret: Bullets will hit rect
		[bullet_index @type:int]
	"""
	def bulletCheck(self, target_rect):
		# generate bullet views
		def _isKillerBullet(bi):
			colli_walls_index = self.bulletsRect[bi].collidelistall(self.wallsRect)
			if len(colli_walls_index) is 0: 
				# clear path between bullet and player
				return True
			# get distance between walls and bullet
			diff_colli_walls = map(lambda wi: abs(self.wallsRect[wi].x-self.bulletsRect[bi].x)+abs(self.wallsRect[wi].y-self.bulletsRect[bi].y), colli_walls_index)
			# choose smallest distance
			diff_walls = reduce(lambda di,dj: di if di<dj else dj, diff_colli_walls)
			# get distance between player and bullet
			diff_player = abs(target_rect.x-self.bulletsRect[bi].x)+abs(target_rect.y-self.bulletsRect[bi].y)
			if diff_player < diff_walls:
				return True
			else:
				return False

		mayHitBulletsIndex = target_rect.collidelistall(self.bulletsView)
		if len(mayHitBulletsIndex) is 0:
			return []
		killerBulletsIndex = filter(lambda bi: _isKillerBullet(bi), mayHitBulletsIndex)
		if len(killerBulletsIndex) is 0:
			return []
		
		return killerBulletsIndex

	"""
	Tank will perform shoot first then move if actions given at same phare
	@ ret
		diff | False
	"""
	def willShootKing(self, dir_offset=0):
		# self.nextMove, self.me, self.walls
		global CASTLE,DIR,MOVE
		log = logging.getLogger()

		direction = (self.me[DIR]+dir_offset)%4

		viewRect = self.getViewRect(self.me[REC], direction, 2)

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
		if rect.top<TOPY or rect.top>BOTY-24 or rect.left<TOPX or rect.left>BOTX-24:
			return -2

		return 0
		
			
	def operations(self,p_mapinfo,c_control):
		log = logging.getLogger()
		debugPath = ["FRONT","RIGHT","BACK","LEFT"]

		pathToGo = []

		prioPathToGo = []

		time_p = time.clock()
		
		while True:
		#-----your ai operation,This code is a random strategy,please design your ai !!-----------------------

			#time.sleep(TIME)
			time_c = time.clock()
			if  abs(time_c - time_p) < TIME:
				continue
			self.Get_mapInfo(p_mapinfo)
			self.updateInfo()
		
		#-------------------------------
			nextDirection = NON
			nextShoot = 0
			checkPoint = None

			# nextMove
			if skip_this:
				#logging.info("Blocking")
				time_p = time_c
				continue 

			# Do Priority Actions
			if len(prioPathToGo) != 0:
				nextShoot = prioPathToGo[0][0]
				nextDirection = prioPathToGo[0][1]
				if self.Update_Strategy(c_control, nextShoot, nextDirection, 0):
					if nextDirection is not NON:
						# Dodge make A-Star* walk path dirty
						pathToGo = []
					del prioPathToGo[0]
				time_p = time_c
				continue

			assert len(prioPathToGo) is 0

			# DIE CHECK
			killerBulletsIndex = self.bulletCheck(self.me[REC])
			if len(killerBulletsIndex) != 0:
				logging.info("killer bullet found")
				actions = map(lambda kbi: self.performActions(kbi), killerBulletsIndex)
				prioPathToGo += reduce(lambda i,j: i+j,actions)

			if len(prioPathToGo) > 0:
				time_p = time_c
				continue

			# check directions, shoot if enemy in shoot range
			# shoot + direction decision (range(1): target lock; range(4): greedy)			
			for i in range(4):
				pointEnemyIndex = self.gunPointingEnemy(i)
				if pointEnemyIndex != -1 and pointEnemyIndex is not None: 
					#logging.info("Enemy %s Me"%debugPath[i])
					if not self.willShootKing(1):
						#logging.info("No King %s Me"%debugPath[i])
						if i == 0:
							nextShoot = 1
						else:
							_dir = (self.me[DIR] + i)%4
							prioPathToGo.append([0, _dir])
							prioPathToGo.append([1, NON])
					else:
						#logging.info("King maybe %s Me"%debugPath[i])
						pointEnemy = self.enemiesRect[pointEnemyIndex]
						enemyDiff  = abs(self.me[REC].x - pointEnemy.x) + abs(self.me[REC].y - pointEnemy.y)
						kingDiff = abs(self.me[REC].x - CASTLE.x) + abs(self.me[REC].y - CASTLE.y)
						if enemyDiff < kingDiff:
							#logging.info("No King %s Me"%debugPath[i])
							if i == 0:
								nextShoot = 1
							else:
								_dir = (self.me[DIR] + i)%4
								prioPathToGo.append([0, _dir])
								prioPathToGo.append([1, NON])

			if len(prioPathToGo) > 0:
				continue

			# direction decision
			if len(prioPathToGo) is 0:
				if pathToGo is None or len(pathToGo) is 0:
					# find an enemy
					target = self.getNextEnemy()
					if target is not None:
						#log.info("next target: (%d,%d)"%(target.x/16, target.y/16))
						pathToGo = self.aStar(target)
					else:
						pathToGo = self.aStar(TOP_GEN)

					if pathToGo is None:
						# newly generated stucked
						prioPathToGo.append([0, UP])
						prioPathToGo.append([1, NON])
						continue
		
			if pathToGo is not None and len(pathToGo) > 0:
				nextDirection = pathToGo[len(pathToGo)-1][0]
				checkPoint = pathToGo[len(pathToGo)-1][1]
				usePathToGo = True

			# move will guild to dead?
			if usePathToGo:
				newMeRect = self.newPosition(self.me[REC], self.me[DIR], nextDirection, self.me[SPD]*2)
				killerBulletsIndex = self.bulletCheck(newMeRect)
				if len(killerBulletsIndex) != 0:
					logging.info("next move will guild to dead")
					usePathToGo = False
					nextDirection = NON

			#log.info("(shoot=%d, nextmove=%d)" % (nextShoot,nextDirection))
			if self.Update_Strategy(c_control, nextShoot, nextDirection, 0):
				if usePathToGo and len(pathToGo) > 0:
					del pathToGo[len(pathToGo)-1]

			time_p = time_c

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
