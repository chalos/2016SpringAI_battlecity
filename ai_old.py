import random
import time
import multiprocessing
import math
import pygame
import Queue

class ai_agent():
	mapinfo = []
	path = "4";
	enemyCount = 0;
	speed=2

	(DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT) = range(4)
	(TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)
	(BASIC, FAST, POWER, ARMOR) = range(4)

	CASTLE = pygame.Rect(12*16, 24*16, 32, 32)

	def __init__(self):
		self.mapinfo = []

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

	"""
	@params
		@player [pygame.Rect(), int DIR, speed, is_shielded]
		* pygame.Rect members:
			(x,y,w,h)
		@titles [[pygame.Rect(), int type]]
	"""
	def colide(self,player,tiles):
		for t in tiles:
			if player[0]-t[0]<=16 or t[0]-player[0]<=26:
				if player[1]-t[1]<=16 or t[1]-player[1]<=26:
					return True
		return False

	"""
	0 <-> 2, 1 <-> 3, 4 --> 4
	"""
	def ops_dir(self,dir):
		return (dir+2)%4 if dir!=4 else dir

	"""
	@params:
		@bullets:
			* [rect, direction, speed]
		@player:
			* [rect, direction, speed, isSheild]
		@enemies:
			* [[rect, direction, speed, type]]
		@speed: 
			* self.speed=6
		@dir_wanted: given from aStar_dir
		@lineup:
			* same column or row (U, R, D, L):(same col up, same row right, same col down, same row left)
		@obstacle_rects:
			* [[rect, type]], which type != GRASS
	"""
	def bulletproof(self,bullets,player,enemies,speed,dir_wanted,lineup,obstacle_rects,debug_msg):
		directions=[]
		nearest_bul=0
		minDist_bul=99999.0 # sys.maxsize

		# player_mid = [player.rect.centerx, player.rect.centery]
		player_mid=[]
		player_mid.append(player[0][0]+13)
		player_mid.append(player[0][1]+13)

		# player_left = player.rect.left
		player_left=player[0][0]
		# player_top = player.rect.top
		player_top=player[0][1]
		shoot=0

		#0 get bullet that has minimum distance with tank
		## (choose a target bullet)
		if len(bullets)>0:
			#1 for bullet in bullets:
			for i in range(len(bullets)):
				#2 dist = sqrt( (bullet.rect.x - player.rect.centerx)^2 + (bullet.rect.y - player.rect.centery)^2 )
				dist=math.sqrt((bullets[i][0][0]-player_mid[0])*(bullets[i][0][0]-player_mid[0])+(bullets[i][0][1]-player_mid[1])*(bullets[i][0][1]-player_mid[1]))
				if dist<minDist_bul:
					nearest_bul=i # nearestBul = bullet
					minDist_bul=dist

		#0 if distance of min_distance(bullet) <= 100
		## (bullet close enough)
		if minDist_bul<=100:
			#1 distance of nearestBul.rect.x -- player.rect.centerx <= 15
			## (bullet will hit player)
			if abs(bullets[nearest_bul][0][0]+1-player_mid[0])<=15:
				#2 distance of nearestBul.rect.x -- player.rect.centerx <=2
				## (but enough to fight back with bullet)
				if abs(bullets[nearest_bul][0][0]+1-player_mid[0])<=2:
					#3 nearestBul.direction == UP, nearestBul.rect.y > player.rect.top
					## (bullet flying up and bullet at down side of player)
					if bullets[nearest_bul][1]==0 and bullets[nearest_bul][0][1]>player_top:
						#4 --> direction queue <-- DOWN
						#4 --> shoot 
						directions.append(2)
						shoot=1
						if debug_msg:
							print "kill bullet from down !!!!"
					#3 nearestBul.distance == DOWN, nearestBul.rect.y < player.rect.top
					## (bullet flying down and bullet at up side of player)
					if bullets[nearest_bul][1]==2 and bullets[nearest_bul][0][1]<player_top:
						#4 --> direction queue <-- UP
						#4 --> shoot
						directions.append(0)
						shoot=1
						if debug_msg:
							print "kill bullet from up !!!!", directions
				#2 distance of nearestBul.rect.x -- player.rect.centerx > 2
				## (cannot fight back with bullet)
				else:
					#3 nearestBul.rect.x > player.rect.centerx
					## (bullet at right side of player)
					if bullets[nearest_bul][0][0]>player_mid[0]:
						#4 --> direction queue <-- LEFT <-- RIGHT
						directions.append(3)
						directions.append(1)
						if debug_msg:
							print "dodge bullet from ud, go left !!!", directions
					#3 nearestBul.rect.x <= player.rect.centerx
					## (bullet at left side of player)
					else:
						#4 --> direction queue <-- RIGHT <-- LEFT
						directions.append(1)
						directions.append(3)
						if debug_msg:
							print "dodge bullet from ud, go right !!!", directions
			
			#1 distance of nearestBul.rect.y -- player.rect.centery <= 15
			## (the bullet will hit player)
			elif abs(bullets[nearest_bul][0][1]+1-player_mid[1])<=15:
				#2 distance of nearestBul.rect.y -- player.rect.centery <= 2
				## (but enough to fight back with bullet)
				if abs(bullets[nearest_bul][0][1]+1-player_mid[1])<=2:
					#3 nearestBul.direction == RIGHT, nearestBul.rect.x < player.rect.x 
					## (bullet flying to right and player at right side of bullet)
					if bullets[nearest_bul][1]==1 and bullets[nearest_bul][0][0]<player_left:
						#4 --> direction queue <-- LEFT
						#4 --> shoot
						directions.append(3)
						shoot=1
						if debug_msg:
							print "kill bullet from left !!!!", directions
					#3 nearestBul.direction == LEFT, nearestBul.rect.x > player.rect.x
					## (bullet flying to left and player at left side of bullet)
					if bullets[nearest_bul][1]==3 and bullets[nearest_bul][0][0]>player_left:
						#4 --> direction queue <-- RIGHT
						#4 --> shoot
						directions.append(1)
						shoot=1
						if debug_msg:
							print "kill bullet from right !!!!", directions
				#2 distance of nearest.rect.y -- player.rect.centery > 2
				## (cannot fight back with bullet)
				else:
					#3 nearestBul.rect.y > player.rect.centery
					## (bullet at down side of player)
					if bullets[nearest_bul][0][1]>player_mid[1]:
						#4 --> direction queue <-- UP <-- DOWN
						directions.append(0)
						directions.append(2)
						if debug_msg:
							print "dodge bullet from lr, go up !!!", directions
					#3 nearestBul.rect.y <= player.rect.centery
					## (bullet at up side of player)
					else:
						#4 --> direction queue <-- DOWN <-- UP
						directions.append(2)
						directions.append(0)
						if debug_msg:
							print "dodge bullet from lr, go down !!!", directions
			#1 bullet distance outside of square (15,15)
			#1 do action on enemy at same column or row
			else:
				#2 aStarDir same as same column/row enemy direction
				if lineup==dir_wanted:
					#3 shoot
					shoot=1
				#2 player.direction same as col/row enemy direction
				if player[1]==lineup:
					#3 --> direction queue <-- Do nothing
					directions.append(4)
				#2 player.direction not same as col/row enemy direction
				else:
					#3 --> direction queue <-- aStarDir
					## should be (col/row enemy direction)?
					directions.append(dir_wanted)

				#2 
				if bullets[nearest_bul][1]==0 or bullets[nearest_bul][1]==2:
					if bullets[nearest_bul][0][0]>player_left:
						if 1 in directions:
							directions.remove(1)
						if debug_msg:
							print "not go into bullet from ud on my right !!!", directions
					else:
						if 3 in directions:
							directions.remove(3)
						if debug_msg:
							print "not go into bullet from ud on my left !!!", directions
				if bullets[nearest_bul][1]==1 or bullets[nearest_bul][1]==3:
					if bullets[nearest_bul][0][1]>player_top:
						if 2 in directions:
							directions.remove(2)
						if debug_msg:
							print "not go into bullet from lr on my down !!!", directions
					else:
						if 0 in directions:
							directions.remove(0)
						if debug_msg:
							print "not go into bullet from lr on my up !!!", directions

		else:
			if lineup==dir_wanted:
				shoot=1
			if player[1]==lineup:
				directions.append(4)
			else:
				directions.append(dir_wanted)

			nearest=0
			minDist=99999
			for i in range(len(enemies)):
				enemies_mid=[enemies[i][0][0]+13,enemies[i][0][1]+13]
				dist=math.sqrt((enemies_mid[0]-player_mid[0])*(enemies_mid[0]-player_mid[0])+(enemies_mid[1]-player_mid[1])*(enemies_mid[1]-player_mid[1]))
				if dist<minDist:
					nearest=i
					minDist=dist
			if minDist<50:
				shoot=1
				if enemies[nearest][1]==0 or enemies[nearest][1]==2:
					if enemies[nearest][0][0]>player_left:
						if 1 in directions:
							directions.append(4)
						if debug_msg:
							print "not go into enemy from ud on my right !!!", directions
					else:
						if 3 in directions:
							directions.append(4)
						if debug_msg:
							print "not go into enemy from ud on my left !!!", directions
				if enemies[nearest][1]==1 or enemies[nearest][1]==3:
					if enemies[nearest][0][1]>player_top:
						if 2 in directions:
							directions.append(4)
						if debug_msg:
							print "not go into enemy from lr on my down !!!", directions
					else:
						if 0 in directions:
							directions.append(4)
						if debug_msg:
							print "not go into enemy from lr on my up !!!", directions

		#print directions,
		if len(directions)>0:
			for direction in directions:
				if direction == 0:
					new_position=[player_left,player_top-speed]
				elif direction == 1:
					new_position=[player_left+speed,player_top]
				elif direction == 2:
					new_position=[player_left,player_top+speed]
				elif direction == 3:
					new_position=[player_left-speed,player_top]
				else:
					new_position=[player_left,player_top]
				player_rect = pygame.Rect(new_position, [26, 26])
				# collisions with tiles
				coli = self.check_barrier(player_rect,obstacle_rects)
				if coli > -2:
					if debug_msg:
						print " c",
					if coli>-1 and self.mapinfo[2][coli][1] == 1:
						if debug_msg:
							print "b"
						if lineup==dir_wanted:
							shoot=1
							break
				else:
					return shoot,direction
		else:
			return shoot,4
		return shoot,4

	def operations (self,p_mapinfo,c_control):

		while True:
		#-----your ai operation,This code is a random strategy,please design your ai !!-----------------------

			time.sleep(self.speed/3)
			self.Get_mapInfo(p_mapinfo)


		#-----varible
			players=self.mapinfo[3]
			player = self.mapinfo[3][0];
			
			obstacle_rects = [];
			# [[rect, direction, speed, type]]
			enemies_list = self.mapinfo[1];
			# [[rect, direction, speed]]
			bullets=self.mapinfo[0]
			
			# player_mid = [player.rect.centerx, player.rect.centery]
			player_mid=[]
			player_mid.append(players[0][0][0]+13)
			player_mid.append(players[0][0][1]+13)
			
			# player_left = player.rect.x
			player_left=players[0][0][0]
			# player_top = player.rect.y
			player_top=players[0][0][1]
			
			lineup=-1
			
			# mapinfo2: tile info [[rect, type]]
			# type: (TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE)
			#0 for each tile
			for rect in self.mapinfo[2]:
				#1 put to obstacle: tile type of brick is not grass
				# * THIS should push TILE_BRICK,TILE_STEEL,TILE_WATER only * @updateObstacleRects
				if rect[1] != 4 or rect[1] < 1:
					obstacle_rects.append(rect[0])

			obs=[]
			# mapinfo2: tile info [[rect, type]]
			#0 for each tile
			for t in self.mapinfo[2]:
				#1 tile type is TILE_BRICK,TILE_STELL,TILE_WATER 
				if t[1]<4:
					obs.append(t[0])
			# obstacle_rects not contains TILE_GRASS; [rect]
			# obs contains only TILE_BRICK,TILE_STELL,TILE_WATER; [rect]
			
			# (DIR_UP, DIR_RIGHT, DIR_DOWN, DIR_LEFT)

			#0 if has enemy do find target enemy + path to target enemy
			if len(enemies_list) > 0 :
				#1 choose enemy h'dist <80 with base, else least h'dist with player
				#1 ret type rect
				enemy_obj = self.enemy_select(player,enemies_list);
				#1 get a string of path: [0-3]*
				self.path = self.a_star(player,enemy_obj,obstacle_rects);
				#1 sting of path deque --> move_dir_aStar or 4
				if len(self.path)>0:
					move_dir_aStar = int(self.path[0])
				else:
					move_dir_aStar =4

				# enemy_mid = [enemy.centerx, enemy.centery]
				enemies_base_mid=[enemy_obj[0]+13,enemy_obj[1]+13]
				#1 enemy.centerx--player.centerx < 13, same column
				if abs(enemies_base_mid[0]-player_mid[0])<13:
					#2 enemy is down side of player
					if enemies_base_mid[1]>player_mid[1]:
						lineup=2
					#2 enemy is up side of player
					else:
						lineup=0
				#1 enemy.centery--player.centery < 13, same row
				#P same column will not response
				if abs(enemies_base_mid[1]-player_mid[1])<13:
					#2 enemy is right side of player
					if enemies_base_mid[0]>player_mid[0]:
						lineup=1
					#2 enemy is left side of player
					else:
						lineup=3

				debug = False
				shoot,move_dir = self.bulletproof(bullets,player,enemies_list,self.speed,move_dir_aStar,lineup,obstacle_rects,debug)
			#0 else do nothing
			else:
				move_dir=4
				shoot = 0


			#-----------
			# base shoot avoid
			if player_mid[0]<12*16+32+17 and player_mid[0]>12*16-17 and (move_dir==2 or move_dir==0):
				shoot=0
			if player_mid[1]>24*16-20:
				shoot=0
			self.Update_Strategy(c_control,shoot,move_dir)
		#------------------------------------------------------------------------------------------------------

	def check_shoot(self,me,enemies):
		enemy_rects = []
		for enemy in enemies:
			enemy_rects.append(enemy[0])
		player_rect = pygame.Rect([me[0].left, me[0].top], [26, 400])
		player_rect2 = pygame.Rect([me[0].left, me[0].top], [500, 26])
		if player_rect.collidelist(enemy_rects) !=1 or player_rect2.collidelist(enemy_rects) !=1 :
			return True;
		return False;

	"""
	@params
		@player: player_rect
			* rect
		@obstacle_rects:
			* [rect], which type != GRASS
	@return
		@type: int
			* -1 player_rect.(x,y) < (0,0), player_rect.(x,y) > (416-26, 416-26) #see Player.move or Enemy.move
			* -2 for player_rect overlap with any obstacle_rects
			* first collision index
	"""
	def check_barrier(self,player,obstacle_rects):
		if player.top < 0 or player.left > (416 - 26) or player.top > (416 - 26) or (player.left < 0):
			return -1;
		idx = player.collidelist(obstacle_rects);
		if idx == -1 :return -2
		else: return idx;

	"""
	@params:
		@player
			* [rect, direction, speed, isSheild]
		@enemy
			* rect
		@obstacle_rects
			* [rect], which type != GRASS
	"""
	def a_star(self,player,enemy,obstacle_rects):
		width = 26;
		# key(str), val(int)
		pathCollection = {"":0}
		# key(str), val(rect)
		pathPosition = {"":player[0]}
		speed = 6#player[0][2]-24
		path ="4";
		# val(rect)
		currentPosition = player[0];
		found = False;
		disable = []

		while not found:
			#0 if number of element in pathCollection not [1,400]
			if (len(pathCollection)<1 or len(pathCollection)>400) :
				#1 path would random generated, break loop
				path = str(random.randint(0, 4))
				print "path too long"
				break;

			# * loop1 -> path=""
			path = min(pathCollection,key = pathCollection.get);
			# * loop1 -> get(""), currentPosition=player.rect
			currentPosition = pathPosition.get(path);
			# * loop1 -> delete "":0
			del pathCollection[path]
			# * loop1 -> delete "":player.rect
			del pathPosition[path]

			#print currentPosition, "totally : ",len(pathCollection) , len(pathPosition) , speed;
			
			# * loop1 -> break if player.rect overlap choosen enemy.rect
			if currentPosition.colliderect(enemy): 
				print "break at overlap"
				break;

			# * loop1 -> disable[] queue player.rect which not overlap with choosen enemy.rect
			disable.append(currentPosition)
			# * loop1 -> lengh=0
			length = len(path)

			# * loop* --> new_position = currentPosition move to up
			new_position = [currentPosition.left, currentPosition.top - speed]
			player_rect = pygame.Rect(new_position, [width, width])
			# * loop1 -> player_rect not no match, player_rect not in disable
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				# * loop1 -> length = 0 + speed = 6 + a.x--b.x + a.y--b.y
				f = self.heuristic(player_rect,enemy,length,speed);
				# * loop1 -> pathPosition queue ""+"0":player_up
				pathPosition.update({path+"0":player_rect})
				# * loop1 -> pathCollection queue ""+"0":6+a.x--b.x+a.y--b.y
				pathCollection.update({path+"0":f})

			# * loop* --> new_position = currentPosition move to right
			new_position = [currentPosition.left+ speed, currentPosition.top]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"1":player_rect})
				pathCollection.update({path+"1":f})

			# * loop* --> new_position = currentPosition move to down
			new_position = [currentPosition.left, currentPosition.top + speed]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"2":player_rect})
				pathCollection.update({path+"2":f})

			# * loop* --> new_position = currentPosition move to left
			new_position = [currentPosition.left-speed, currentPosition.top]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"3":player_rect})
				pathCollection.update({path+"3":f})

		# path [0-3]*
		# (UP, RIGHT, DOWN, LEFT) = (0,1,2,3)
		print path
		return path;

	"""
	@params:
		@player:
			* rect
		@enemy:
			* rect
		@length:
		@speed:
	@return
		@type:
			* int
		@value:
			* length+speed + player.x--enemy.x + player.y--enemy.y
	"""
	def heuristic(self,player,enemy,length,speed):
		g = length*speed;
		h = abs(player.left-enemy.left)+ abs(player.top-enemy.top);
		return g+h;

	"""
	@ param:
		@ player: [rect, direction, speed, isSheild]
		@ enemies: [[rect, direction, speed, type]]
	@ explaination: 
		* return enemy.rect in piority
		* least h'dist which <80 with base --> h'dist least with player
	"""
	def enemy_select(self,player,enemies):
		# enemies[0].rect(x,y,w,h)
		result_base = enemies[0][0]
		distance_base = 999999;
		#0 choose a enemy which h'distance is too close to base
		for enemy in enemies:
			#1 h'distance = enemy.rect.x--base.rect.x + enemy.rect.y--base.rect.y
			h = abs(enemy[0].left- 12*16)+abs(enemy[0].top-24*16);
			if h < distance_base:
				distance_base = h;
				result_base = enemy[0];

		result_me = enemies[0][0]
		distance_me = 999999;
		#0 choose a enemy which h'distance is too close to player
		for enemy in enemies:
			#1 h'distance = enemy.rect.x--player.rect.x + enemy.rect.y--player.rect.y
			h = abs(enemy[0].left- player[0].left)+abs(enemy[0].top-player[0].top);
			if h < distance_me:
				distance_me = h;
				result_me = enemy[0];

		# choose enemy h'distance < 80 with base
		# else choose h'distance least with player
		if distance_base<80:
			result=result_base
		else:
			result=result_me
		return result;

	"""
	@ explanation:
		* return enemy.rect that h'distance smallest with base
	"""
	def whoDangerous(self,enemies):
		result = enemies[0][0]
		distance = 999999;
		for enemy in enemies:
			h = abs(enemy[0].left- 12*16)+abs(enemy[0].top-24*16);
			if h < distance:
				distance = h;
				result = enemy[0];
		return result;

	def Get_mapInfo(self,p_mapinfo):
		if p_mapinfo.empty()!=True:
			try:
				self.mapinfo = p_mapinfo.get(False)
			except Queue.Empty:
				skip_this=True

	def Update_Strategy(self,c_control,shoot,move_dir,keep_action=1):
		if c_control.empty() ==True:
			c_control.put([shoot,move_dir,keep_action])
			return True
		else:
			return False

