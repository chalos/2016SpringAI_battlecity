import random
import time
import multiprocessing
import math
class ai_agent():
	mapinfo = []
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

	sameDir=0
	dirCount=0

	def operations (self,p_mapinfo,c_control):	

		while True:
		#-----your ai operation,This code is a random strategy,please design your ai !!-----------------------
			self.Get_mapInfo(p_mapinfo)
			print 0,self.mapinfo[0]
			print 1,self.mapinfo[1]
			print 2,self.mapinfo[2]
			print 3,self.mapinfo[3]
			enemies=self.mapinfo[1]
			players=self.mapinfo[3]
			player_mid=[]
			player_mid.append(players[0][0][0]+13)
			player_mid.append(players[0][0][1]+13)
			play_dir=players[0][1]
			#time.sleep(0.001)
			q=0
			for i in range(10000000):
				q+=1



			if len(enemies)>0:
				nearest=0
				minDist=99999
				for i in range(len(enemies)):
					dist=math.sqrt((enemies[i][0][0]-208)*(enemies[i][0][0]-208)+(enemies[i][0][1]-400)*(enemies[i][0][1]-400))
					if dist<minDist:
						nearest=i
						minDist=dist
				print "Nearest enemy:",enemies[nearest]
				if self.dirCount==0:
					if enemies[nearest][0][0]>players[0][0][0]:
						move_dir=1
					elif abs(enemies[nearest][0][0]-players[0][0][0])<13:
						move_dir=move_dir
					else:
						move_dir=3
					if enemies[nearest][0][1]>players[0][0][1]:
						move_dir=2
					elif abs(enemies[nearest][0][1]-players[0][0][1])<13:
						move_dir=move_dir
					else:
						move_dir=0
					self.dirCount=1
				else:
					if enemies[nearest][0][1]>players[0][0][1]:
						move_dir=2
					elif abs(enemies[nearest][0][1]-players[0][0][1])<13:
						move_dir=move_dir
					else:
						move_dir=0
					if enemies[nearest][0][0]>players[0][0][0]:
						move_dir=1
					elif abs(enemies[nearest][0][0]-players[0][0][0])<13:
						move_dir=move_dir
					else:
						move_dir=3
					self.dirCount=0
			else:
				move_dir=4

			#move_dir = 3 #random.randint(0,4)
			#-----------
			shoot = 1 #random.randint(0,1)
			print "Player: ",player_mid,play_dir
			if player_mid[0]<12*16+42 and player_mid[0]>12*16-10 and move_dir==2:
				shoot=0
			if player_mid[1]>24*16-20 and ((player_mid[0]<12*16 and move_dir==1) or (player_mid[0]>12*16+32 and move_dir==3)):
				shoot=0
			print "Update: ",shoot,move_dir
			self.Update_Strategy(c_control,shoot,move_dir)
		#------------------------------------------------------------------------------------------------------

	def Get_mapInfo(self,p_mapinfo):
		if p_mapinfo.empty()!=True:
			try:
				self.mapinfo = p_mapinfo.get(False)
			except Queue.Empty:
				skip_this=True

	def Update_Strategy(self,c_control,shoot,move_dir):
		if c_control.empty() ==True:
			c_control.put([shoot,move_dir])

