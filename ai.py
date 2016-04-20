import random
import time
import multiprocessing
import math
import pygame

class ai_agent():
	mapinfo = []
	path = "4";
	enemyCount = 0;
	speed=6
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

	def colide(self,player,tiles):
		for t in tiles:
			if player[0]-t[0]<=16 or t[0]-player[0]<=26:
				if player[1]-t[1]<=16 or t[1]-player[1]<=26:
					return True
		return False

	def ops_dir(self,dir):
		return (dir+2)%4


	def bulletproof(self,bullets,player,enemies,speed,dir_wanted,lineup,obstacle_rects,debug_msg):
		directions=[]
		nearest_bul=0
		minDist_bul=99999.0
		player_mid=[]
		player_mid.append(player[0][0]+13)
		player_mid.append(player[0][1]+13)
		player_left=player[0][0]
		player_top=player[0][1]
		shoot=0
		if len(bullets)>0:
			for i in range(len(bullets)):
				dist=math.sqrt((bullets[i][0][0]-player_mid[0])*(bullets[i][0][0]-player_mid[0])+(bullets[i][0][1]-player_mid[1])*(bullets[i][0][1]-player_mid[1]))
				if dist<minDist_bul:
					nearest_bul=i
					minDist_bul=dist
		if minDist_bul<=100:
			if abs(bullets[nearest_bul][0][0]+1-player_mid[0])<=15:
				if abs(bullets[nearest_bul][0][0]+1-player_mid[0])<=2:
					if bullets[nearest_bul][1]==0 and bullets[nearest_bul][0][1]>player_top:
						directions.append(2)
						shoot=1
						if debug_msg:
							print "kill bullet from down !!!!"
					if bullets[nearest_bul][1]==2 and bullets[nearest_bul][0][1]<player_top:
						directions.append(0)
						shoot=1
						if debug_msg:
							print "kill bullet from up !!!!", directions
				else:
					if bullets[nearest_bul][0][0]>player_mid[0]:
						directions.append(3)
						directions.append(1)
						if debug_msg:
							print "dodge bullet from ud, go left !!!", directions
					else:
						directions.append(1)
						directions.append(3)
						if debug_msg:
							print "dodge bullet from ud, go right !!!", directions
			elif abs(bullets[nearest_bul][0][1]+1-player_mid[1])<=15:
				if abs(bullets[nearest_bul][0][1]+1-player_mid[1])<=2:
					if bullets[nearest_bul][1]==1 and bullets[nearest_bul][0][0]<player_left:
						directions.append(3)
						shoot=1
						if debug_msg:
							print "kill bullet from left !!!!", directions
					if bullets[nearest_bul][1]==3 and bullets[nearest_bul][0][0]>player_left:
						directions.append(1)
						shoot=1
						if debug_msg:
							print "kill bullet from right !!!!", directions
				else:
					if bullets[nearest_bul][0][1]>player_mid[1]:
						directions.append(0)
						directions.append(2)
						if debug_msg:
							print "dodge bullet from lr, go up !!!", directions
					else:
						directions.append(2)
						directions.append(0)
						if debug_msg:
							print "dodge bullet from lr, go down !!!", directions
			else:
				if lineup==dir_wanted:
					shoot=1
				if player[1]==lineup:
					directions.append(4)
				else:
					directions.append(dir_wanted)

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

			time.sleep(self.speed/100)
			self.Get_mapInfo(p_mapinfo)


		#-----varible
			players=self.mapinfo[3]
			player = self.mapinfo[3][0];
			obstacle_rects = [];
			enemies_list = self.mapinfo[1];
			bullets=self.mapinfo[0]
			player_mid=[]
			player_mid.append(players[0][0][0]+13)
			player_mid.append(players[0][0][1]+13)
			player_left=players[0][0][0]
			player_top=players[0][0][1]
			lineup=-1
			for rect in self.mapinfo[2]:
				if rect[1] != 4 or rect[1] < 1:
					obstacle_rects.append(rect[0])

			obs=[]
			for t in self.mapinfo[2]:
				if t[1]<4:
					obs.append(t[0])

			if len(enemies_list) > 0 :
				enemy_obj = self.enemy_select(player,enemies_list);
				self.path = self.a_star(player,enemy_obj,obstacle_rects);
				if len(self.path)>0:
					move_dir_aStar = int(self.path[0])
				else:
					move_dir_aStar =4

				enemies_base_mid=[enemy_obj[0]+13,enemy_obj[1]+13]
				if abs(enemies_base_mid[0]-player_mid[0])<13: #same column
					if enemies_base_mid[1]>player_mid[1]:
						lineup=2
					else:
						lineup=0

				if abs(enemies_base_mid[1]-player_mid[1])<13: #same row
					if enemies_base_mid[0]>player_mid[0]:
						lineup=1
					else:
						lineup=3

				shoot,move_dir = self.bulletproof(bullets,player,enemies_list,self.speed,move_dir_aStar,lineup,obstacle_rects,True)
			else:
				move_dir=4
				shoot = 0


			#-----------
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

	def check_barrier(self,player,obstacle_rects):
		if player.top < 0 or player.left > (416 - 26) or player.top > (416 - 26) or (player.left < 0):
			return -1;
		idx = player.collidelist(obstacle_rects);
		if idx == -1 :return -2
		else: return idx;

	def a_star(self,player,enemy,obstacle_rects):
		width = 25;
		pathCollection = {"":0}
		pathPosition = {"":player[0]}
		speed = 6#player[0][2]-24
		path ="4";
		currentPosition = player[0];
		found = False;
		disable = []

		while not found:
			if (len(pathCollection)<1 or len(pathCollection)>400) :
				if len(pathCollection)>500:
					print "path too long"
				path = str(random.randint(0, 4))
				break;
			path = min(pathCollection,key = pathCollection.get);
			currentPosition = pathPosition.get(path);
			del pathCollection[path]
			del pathPosition[path]

			#print currentPosition, "totally : ",len(pathCollection) , len(pathPosition) , speed;
			if currentPosition.colliderect(enemy): break;

			disable.append(currentPosition)
			length = len(path)

			new_position = [currentPosition.left, currentPosition.top - speed]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				#print "up"
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"0":player_rect})
				pathCollection.update({path+"0":f})

			new_position = [currentPosition.left+ speed, currentPosition.top]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				#print "right"
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"1":player_rect})
				pathCollection.update({path+"1":f})

			new_position = [currentPosition.left, currentPosition.top + speed]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				#print "down"
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"2":player_rect})
				pathCollection.update({path+"2":f})

			new_position = [currentPosition.left-speed, currentPosition.top]
			player_rect = pygame.Rect(new_position, [width, width])
			if self.check_barrier(player_rect,obstacle_rects) == -2 and (player_rect not in disable):
				#print "left"
				f = self.heuristic(player_rect,enemy,length,speed);
				pathPosition.update({path+"3":player_rect})
				pathCollection.update({path+"3":f})


		return path;

	def heuristic(self,player,enemy,length,speed):
		g = length*speed;
		h = abs(player.left-enemy.left)+ abs(player.top-enemy.top);
		return g+h;

	def enemy_select(self,player,enemies):
		result_base = enemies[0][0]
		distance_base = 999999;
		for enemy in enemies:
			h = abs(enemy[0].left- 12*16)+abs(enemy[0].top-24*16);
			if h < distance_base:
				distance_base = h;
				result_base = enemy[0];
		result_me = enemies[0][0]
		distance_me = 999999;
		for enemy in enemies:
			h = abs(enemy[0].left- player[0].left)+abs(enemy[0].top-player[0].top);
			if h < distance_me:
				distance_me = h;
				result_me = enemy[0];

		if distance_base<80:
			result=result_base
		else:
			result=result_me
		return result;

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

	def Update_Strategy(self,c_control,shoot,move_dir):
		if c_control.empty() ==True:
			c_control.put([shoot,move_dir])

