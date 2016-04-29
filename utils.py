 import pygame

(BUL,ENE,TIL,ME) = range(4)
(UP, RIGHT, DOWN, LEFT, NON) = range(5)
(TILE_EMPTY, TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_GRASS, TILE_FROZE) = range(6)
(BASIC, FAST, POWER, ARMOR) = range(4)
(REC,DIR,SPD,ETY) = range(4)
CASTLE = pygame.Rect(12*16, 24*16, 32, 32)
SHL=3
TTY=1
UNMOVABLE = Set([TILE_BRICK, TILE_STEEL, TILE_WATER, TILE_FROZE])
(TOPX, TOPY, BOTX, BOTY) = (0,0,416, 416)
(SHOOT,MOVE) = range(2)

"""
Manhattan distance based
@param
	s, t pygame.Rect, speed int
@ret 
	int
"""

def huristic(s, t, speed, weight=1):
	h = diff(s,t) / SPEED
	return weight * h

def diff(s, t):
	return (abs(s.x - t.x) + abs(s.y - t.y))

def nearest(num, base):
	""" Round number to nearest divisible """
	return int(round(num / (base * 1.0)) * base)

def fixPosition(target):
	new_x = nearest(target.left, 8) + 3
	new_y = nearest(target.top, 8) + 3

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
def newPosition(origin, old_direction, new_direction, speed):
	copyOrigin = pygame.Rect(origin.x, origin.y, origin.w, origin.h)
	if old_direction != new_direction:
		new_x = nearest(copyOrigin.left, 8) + 3
		new_y = nearest(copyOrigin.top, 8) + 3
		if (abs(copyOrigin.left - new_x) < 5):
			copyOrigin.left = new_x
		if (abs(copyOrigin.top - new_y) < 5):
			copyOrigin.top = new_y

	if new_direction == UP:
		copyOrigin.move_ip(0, -speed)
	elif new_direction == RIGHT:
		copyOrigin.move_ip(speed, 0)
	elif new_direction == DOWN:
		copyOrigin.move_ip(0, speed)
	elif new_direction == LEFT:
		copyOrigin.move_ip(-speed, 0)

	return copyOrigin
