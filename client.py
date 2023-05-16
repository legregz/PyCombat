import socket
import select
import sys
import _thread
import pygame
import time
import random
from common import *

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) == 3:
	#if there is 3 arguments then connect to the adress and the port given in arguents
	server.connect((str(sys.argv[1]), int(sys.argv[2])))
else:
	#else connect to the public server
	server.connect(("188.165.247.59", 55352))

#initialize global variables
Name = ""
user_data = {}

players = {}
boxes = {}
zones = {}
messages = []
end = 0

#function draw() is a shortcut of screen.blit() and center image given on y or/and x axis
def draw(image, xy, x_centered = True, y_centered = True):
	pos = image.get_rect()
	pos.center = xy
	x, y = xy
	if x_centered == True:
		x = pos[0]
	if y_centered == True:
		y = pos[1]
	screen.blit(image, (x, y))

class Player:
	def __init__(self, name, position, life, direction, skin, weapon, care, score):
		#init Player's variables
		self.name = name
		self.position = position
		self.life = life
		self.direction = direction
		self.dead = False
		self.skin = skin
		self.score = score
		self.weapon = eval(weapon + "()")
		self.care = eval(care + "()")
		self.respawn_time = 0
		self.trace_time = 0
		self.heal_time = 0
		self.hurted_time = 0
		self.zone_time = 0
		self.damages = 0
		self.texture = pygame.image.load(f".PyCombat/textures/{self.skin}/{self.direction}.png").convert_alpha()
		self.show()

	#function show blit the player on the screen
	def show(self):
		#if player not dead
		if self.dead == False:
			#if player hurted
			if self.hurted_time > time.time():
				rand_x = random.randint(-2, 2)
				rand_y = random.randint(-2, 2)
				
				screen.blit(self.texture, (self.position[0] - 16 + rand_x, self.position[1] - 16 + rand_y))
				draw(font.render(self.name, True, (255,255,255)), (self.position[0] + rand_y, self.position[1] - 32 + rand_x))
				draw(font.render("-" + str(self.damages), True, (255, 0, 0)), (self.position[0], self.position[1] - 48 + int((self.hurted_time - time.time()) * 100)))
				pygame.draw.line(screen, (255, 0, 0), (self.position[0] - 20 + rand_y, self.position[1] - 22 + rand_x), (int(self.position[0] - 20 + self.life + rand_x), self.position[1] - 22 + rand_y), 4)
			else:
				draw(font.render(self.name, True, (255,255,255)), (self.position[0], self.position[1] - 32))
				pygame.draw.line(screen, (255, 0, 0), (self.position[0] - 20, self.position[1] - 22), (int(self.position[0] - 20 + self.life), self.position[1] - 22), 4)
				screen.blit(self.texture, (self.position[0] - 16, self.position[1] - 16))

			#if player attack
			if self.trace_time > time.time():
				trace = pygame.image.load(f".PyCombat/textures/air_trace/{self.direction}.png").convert_alpha()
				
				if self.direction == "bottom":
					screen.blit(trace, (self.position[0] - 16 + self.rand_x, self.position[1] + 16 + self.rand_y))
				elif self.direction == "top":
					screen.blit(trace, (self.position[0] - 16 + self.rand_x, self.position[1] - 48 + self.rand_y))
				elif self.direction == "right":
					screen.blit(trace, (self.position[0] + 16 + self.rand_x, self.position[1] - 16 + self.rand_y))
				elif self.direction == "left":
					screen.blit(trace, (self.position[0] - 48 + self.rand_x, self.position[1] - 16 + self.rand_y))
			
			#if player heal himself
			if self.heal_time > time.time():
				draw(font.render("+" + str(self.care.pvs), True, (255, 0, 0)), (self.position[0], self.position[1] - 48 + int((self.heal_time - time.time()) * 100)))
		
		#if player dead
		elif self.dead == True:
			if self.respawn_time - 4.7 >= time.time():
				#draw the lightning when the player dead
				pygame.draw.line(screen, (235, 235, 255), (self.position[0], 0), (self.position[0] + 30, self.position[1] // 3), 6)
				pygame.draw.line(screen, (235, 235, 255), (self.position[0] + 30, self.position[1] // 3), (self.position[0] - 30, self.position[1] * 2 // 3), 5)
				pygame.draw.line(screen, (235, 235, 255), (self.position[0] - 30, self.position[1] * 2 // 3), (self.position[0], self.position[1]), 4)
			
			#if player is you
			if self.name == Name:
				#draw the time before your respawn
				draw(font3.render("Respawn in " + str(int(self.respawn_time - time.time())), True, (255,255,255)), (lenght // 2, width // 2))
				#if time before respawn is down
				if self.respawn_time <= time.time():
					#set the player's state to alive
					self.death(False)

		for key in list(zones.keys()):
			#if player is in a zone
			if zones[key].position[0] - 30 < self.position[0] < zones[key].position[0] + 30 and zones[key].position[1] - 30 < self.position[1] < zones[key].position[1] + 30:

				nobody = True
				for key2 in list(players.keys()):
					if key2 != Name:
						if zones[key].position[0] - 30 < players[key2].position[0] < zones[key].position[0] + 30 and zones[key].position[1] - 30 < players[key2].position[1] < zones[key].position[1] + 30:
							nobody = False
							break
				
				#if there is nobody in the zone
				if nobody == True:
					#add 1 point to the player
					draw(font.render("+1", True, (0, 255, 0)), (self.position[0], self.position[1] - 48 + int((self.zone_time - 0.9 - time.time()) * 50)))
					if self.zone_time < time.time():
						self.score += 1
						self.zone_time = time.time() + 1

	def move(self, move):
		#if player is not dead
		if self.dead == False:
			#changer position of player
			self.position[0] += move[0]
			self.position[1] += move[1]
			
			#change direction of player in function of movement
			if move[1] > 0:
				self.direction = "bottom"
			elif move[1] < 0:
				self.direction = "top"
			if move[0] > 0:
				self.direction = "right"
			elif move[0] < 0:
				self.direction = "left"

			self.texture = pygame.image.load(f".PyCombat/textures/{self.skin}/{self.direction}.png").convert_alpha()
			#send to other players the player's movement
			server.send(bytes(str(['@Move', self.name, self.position, self.direction]), "utf-8"))

	def attack(self):
		#if player is you
		if self.name == Name:
			#if you're not dead
			if self.dead == False:
				server.send(bytes(str(['@Attack', self.name]), "utf-8"))
				self.weapon.durability -= 1

				#delete the weapon if his durability is equal to 0
				if self.weapon.durability == 0:
					self.weapon = hand()
					server.send(bytes(str(['@Weapon', self.name, self.weapon.name]), "utf-8"))

		self.trace_time = time.time() + 0.1
		self.rand_x = random.randint(- 2, 2)
		self.rand_y = random.randint(- 2, 2)
		
	def heal(self):
		#if player is you
		if self.name == Name:
			#if you're not dead
			if self.dead == False:
				if self.care.pvs != 0:
					self.heal_time = time.time() + 0.1
					self.life += self.care.pvs

					#block your life at the maximum of 40
					if self.life > 40:
						self.life = 40

					server.send(bytes(str(['@Life', self.name, self.life]), "utf-8"))
					self.care.durability -= 1

					#delete the care if his durability is equal to 0
					if self.care.durability == 0:
						self.care = hand_care()
						server.send(bytes(str(['@Care', self.name, self.care.name]), "utf-8"))

	def hurted(self, name, weapon, position):
		#if you're not dead
		if self.dead == False:
			#if you are into the reach around the given position
			if abs(position[0] - self.position[0]) < 48 and abs(position[1] - self.position[1]) < 48:
				self.hurted_time = time.time() + 0.1
				self.life -= weapon.damages
				self.damages = weapon.damages
				server.send(bytes(str(['@Life', self.name, self.life]), "utf-8"))
				
				#knockback your player in function of direction of player who hurted you
				if players[name].direction == "right":
					self.position[0] += 10
				elif players[name].direction == "left":
					self.position[0] -= 10
				elif players[name].direction == "top":
					self.position[1] -= 10
				elif players[name].direction == "bottom":
					self.position[1] += 10	
				server.send(bytes(str(['@Move', self.name, self.position, self.direction]), "utf-8"))

				#if your life < 1 then set your player in state of dead
				if self.life < 1:
					self.respawn_time = time.time() + 5
					self.death(True)
			
	def death(self, dead):
		self.dead = dead
		#if you're not dead
		if dead == False:
			#put your life at 40
			self.life = 40
			server.send(bytes(str(['@Life', self.name, self.life]), "utf-8"))
			#put your player at a random position
			self.position = [random.randint(4, (lenght-32) // 10) * 10, random.randint(4, (width-32) // 10) * 10]
			server.send(bytes(str(['@Move', self.name, self.position, self.direction]), "utf-8"))
			
		server.send(bytes(str(['@Death', self.name, self.dead]), "utf-8"))
		
	def player(self):
		server.send(bytes(str(["@Player", self.name, self.position, self.life, self.direction, self.skin, self.weapon.name, self.care.name, self.score]), "utf-8"))

class Zone:
	def __init__(self, name, position, end):
		self.name = name
		self.position = [position[0] * 10, position[1] * 10]
		self.end = end
	def show(self):
		rect = (self.position[0] - 30, self.position[1] - 30, 60, 60)
		shape_surf = pygame.Surface(pygame.Rect(rect).size, pygame.SRCALPHA)
		pygame.draw.rect(shape_surf, (255, 255, 0, 200), shape_surf.get_rect())
		pygame.draw.rect(shape_surf, (255, 255, 0, 255), shape_surf.get_rect(), 4)
		screen.blit(shape_surf, rect)
		pygame.draw.line(screen, (0, 255, 0), (self.position[0] - 20, self.position[1] - 40), (self.position[0] - 20 + int((self.end - time.time()) * 2), self.position[1] - 40), 4)

class Box:
	def __init__(self, name, position, end, loot):
		self.name = name
		self.position = [position[0] * 10, position[1] * 10]
		self.end = end
		self.loot = loot
		self.texture = pygame.image.load(".PyCombat/textures/boxes/box.png").convert_alpha()

	def show(self):
		if self.end - 2 > time.time():
			screen.blit(self.texture, (self.position[0] - 16, self.position[1] - 16))
			pygame.draw.line(screen, (0, 255, 0), (self.position[0] - 10, self.position[1] - 18), (self.position[0] - 10 + int((self.end - time.time()) * 2), self.position[1] - 18), 4)
		elif self.end -2 < time.time() < self.end:
			rand_x = random.randint(-1, 1)
			rand_y = random.randint(-1, 1)
			screen.blit(self.texture, (self.position[0] - 16 + rand_x, self.position[1] - 16 + rand_y))
			pygame.draw.line(screen, (0, 255, 0), (self.position[0] - 10 + rand_y, self.position[1] - 18 + rand_x), (self.position[0] - 10 + int((self.end - time.time()) * 2) + rand_x, self.position[1] - 18 + rand_y), 4)
		else:
			del(boxes[self.name])
			
	def hurted(self, position):
		if abs(position[0] - self.position[0]) < 48 and abs(position[1] - self.position[1]) < 48:
			server.send(bytes(str(['@Taken', self.name]), "utf-8"))
			loot = eval((self.loot + "()"))
			if loot.type == "weapon":
				players[Name].weapon = loot
				server.send(bytes(str(['@Weapon', players[Name].name, players[Name].weapon.name]), "utf-8"))
			if loot.type == "care":
				players[Name].care = loot
				server.send(bytes(str(['@Care', players[Name].name, players[Name].care.name]), "utf-8"))
			del(boxes[self.name])
			
class Button:
	def __init__(self, rect, func, text = '', color = ''):
		self.rect = rect
		self.func = func
		self.color = color
		self.text = text
		self.error = ""
	
	def on_click(self, pos, arg):
		if self.rect[0] - (self.rect[2] / 2) < pos[0] < self.rect[0] + (self.rect[2] / 2) and self.rect[1] - (self.rect[3] / 2) < pos[1] < self.rect[1] + (self.rect[3] / 2):
			self.error = eval(self.func + arg)
			if len(str(self.error)) == 0:
				return True
			
	def show(self):
		pygame.draw.rect(screen, self.color, (self.rect[0] - self.rect[2] // 2, self.rect[1] - self.rect[3] // 2, self.rect[2], self.rect[3]))
		draw(font.render(self.text, True, (255,255,255)), (self.rect[0], self.rect[1]))
		if type(self.error) == str:
			draw(font.render(self.error, True, (255,0,0)), (self.rect[0], self.rect[1] - self.rect[3] // 2 - 10))
		
class Entry:
	def __init__(self, rect, color = '', initial_text = ''):
		self.rect = rect
		self.color = color
		self.initial_text = initial_text
		self.clicked = False
		self.text = ''
		self.repeat_time = 0
		
	def on_click(self, pos):
		if self.rect[0] - (self.rect[2] / 2) < pos[0] < self.rect[0] + (self.rect[2] / 2) and self.rect[1] - (self.rect[3] / 2) < pos[1] < self.rect[1] + (self.rect[3] / 2):
			self.clicked = True
		else:
			self.clicked = False

	def show(self, char):
		if self.clicked == True and self.repeat_time < time.time():
			self.repeat_time = time.time() + 0.01
			if char == "\b":
				self.text = self.text[:-1]
			else:
				self.text += char

		pygame.draw.rect(screen, self.color, (self.rect[0] - self.rect[2] // 2, self.rect[1] - self.rect[3] // 2, self.rect[2], self.rect[3]))
		if len(self.text) > 0:
			draw(font.render(self.text, True, (0, 0, 0)), (self.rect[0] - self.rect[2] // 2, self.rect[1]), x_centered = False, y_centered = True)
		else:
			draw(font.render(self.initial_text, True, (150, 150, 150)), (self.rect[0] - self.rect[2] // 2, self.rect[1]), x_centered = False, y_centered = True)
		return self.text

def floatless(nb):
	if int(nb) / nb == 1:
		return int(nb)
	else:
		return nb

def game():
	global fps, run
	
	time_fps = time.time()
	fps_now = 0
	fps = 0
	run = True
	
	while run == True:
		if time_fps + 1 <= time.time():
			fps = fps_now
			fps_now = 0
			time_fps = time.time()
			
		move = [0, 0]
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False

			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_s:
					if players[Name].position[1] < width - 32:
						move[1] = 10
					
				if event.key == pygame.K_z:
					if players[Name].position[1] > 32:
						move[1] = -10
					
				if event.key == pygame.K_q:
					if players[Name].position[0] > 32:
						move[0] = -10
					
				if event.key == pygame.K_d:
					if players[Name].position[0] < lenght - 32:
						move[0] = 10
						
				if event.key == pygame.K_COLON:
					chat()
					
			if event.type == pygame.MOUSEBUTTONDOWN:
				if pygame.mouse.get_pressed()[0] == 1:
					players[Name].attack()
					for elt in list(boxes.keys()):
						boxes[elt].hurted(players[Name].position)
				if pygame.mouse.get_pressed()[2] == 1:
					players[Name].heal()
				
		if move[0] != 0 or move[1] != 0:
			players[Name].move(move)
		refresh()
		pygame.display.flip()
		fps_now += 1
		
	return players[Name].score

def listen():
	global run, end, players
	init = True
	sockets_list = [sys.stdin, server]
	read_sockets, write_socket, error_socket = select.select(sockets_list,[],[])
	while True:
		evaluate_msg = " "

		for socks in read_sockets:
			if socks == server:
				try:
					msgs = separate(socks.recv(2048).decode())
				except:
					print("Connexion interrompue")
					_thread.exit()

				for msg in msgs:
					if msg[0] == "[" and msg[-1] == "]":
						evaluate_msg = eval(msg)

					if init == True:
						if evaluate_msg[0] == "@Welcome":
							players[Name].player()
						if evaluate_msg[0] == "@Go":
							init = False
					
					else:
						if evaluate_msg[0] == "@Move":
							players[evaluate_msg[1]].position = evaluate_msg[2]
							players[evaluate_msg[1]].direction = evaluate_msg[3]
							players[evaluate_msg[1]].texture = pygame.image.load(f".PyCombat/textures/{players[evaluate_msg[1]].skin}/{players[evaluate_msg[1]].direction}.png").convert_alpha()

						elif evaluate_msg[0] == "@Attack":
							players[Name].hurted(players[evaluate_msg[1]].name, players[evaluate_msg[1]].weapon, players[evaluate_msg[1]].position)
							players[evaluate_msg[1]].attack()

						elif evaluate_msg[0] == "@Life":
							if players[evaluate_msg[1]].life > evaluate_msg[2]:
								players[evaluate_msg[1]].damages = floatless(players[evaluate_msg[1]].life - evaluate_msg[2])
								players[evaluate_msg[1]].hurted_time = time.time() + 0.1
							players[evaluate_msg[1]].life = evaluate_msg[2]
							
						elif evaluate_msg[0] == "@Death":
							players[evaluate_msg[1]].dead = evaluate_msg[2]
							players[evaluate_msg[1]].respawn_time = time.time() + 5
							
						elif evaluate_msg[0] == "@Taken":
							try:
								del(boxes[evaluate_msg[1]])
							except:
								pass
							
						elif evaluate_msg[0] == "@Weapon":
							players[evaluate_msg[1]].weapon = eval(evaluate_msg[2] + "()")
						
						elif evaluate_msg[0] == "@Message":
							messages.append(evaluate_msg[1])
							
						elif evaluate_msg[0] == "@Quit":
							try:
								del(players[evaluate_msg[1]])
								print("Player named " + evaluate_msg[1] + " has been deleted")
							except:
								print("Player named " + evaluate_msg[1] + " is already deleted")
						
					if evaluate_msg[0] == "@Player":
						players[evaluate_msg[1]] = Player(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4], evaluate_msg[5], evaluate_msg[6], evaluate_msg[7], evaluate_msg[8])
						
					elif evaluate_msg[0] == "@Box":
						boxes[evaluate_msg[1]] = Box(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4])
						
					elif evaluate_msg[0] == "@Zone":
						zones[evaluate_msg[1]] = Zone(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3])
						
					elif evaluate_msg[0] == "@End":
						run = False
						for key in list(players.keys()):
							if key != Name:
								del(players[key])
						_thread.exit()
						
					elif evaluate_msg[0] == "@Time":
						end = evaluate_msg[1]

pygame.init()
screen = pygame.display.set_mode((lenght + 200, width))
pygame.display.set_caption("Combat")

font = pygame.font.Font(".PyCombat/LiberationMono-Bold.ttf", 10)
font3 = pygame.font.Font(".PyCombat/LiberationMono-Bold.ttf", 30)

pygame.key.set_repeat(1, 30)

def refresh():
	screen.fill(0)
	
	minimum = 0
	if len(messages) > 32:
		minimum = len(messages) - 32
	for i in range(minimum, len(messages)):
		screen.blit(font.render(messages[i], True, (255,255,255)), (lenght, (i - minimum) * 15))
	
	for i in list(zones.keys()):
		zones[i].show()
	try:
		for elt in list(boxes.keys()):
			boxes[elt].show()
	except:
		pass

	for i in range(len(players.keys()) - 1, -1, -1):
		players[list(players.keys())[i]].show()

	screen.blit(font.render(str(fps), True, (255,255,255)), (10, 10))
	screen.blit(font.render(players[Name].weapon.name, True, (255,255,255)), (10, 20))
	screen.blit(font.render(players[Name].care.name, True, (255,255,255)), (10, 30))
	screen.blit(font.render(str(players[Name].score), True, (255, 255, 255)), (10, 40))
	screen.blit(font.render(str(int(end - time.time())), True, (255, 255, 255)), (10, 50))

def chat():
	time.sleep(0.2)
	global run
	label = font.render(":", True, (255,255,255))
	user_text = ''
	repeat_time = 0
	
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				run = False
				return ''
				
			if event.type == pygame.KEYDOWN and repeat_time < time.time():
				repeat_time = time.time() + 0.1
				
				if event.key == pygame.K_BACKSPACE:
					user_text = user_text[:-1]
				else:
					if event.key != pygame.K_RETURN:
						user_text += event.unicode
					
				if event.key == pygame.K_RETURN:
					if len(user_text) > 0:
						server.send(bytes(str(["@Message", "<" + Name + "> " + user_text]), "utf-8"))
						messages.append("<" + Name + "> " + user_text)
						user_text =''
					
				if event.key == pygame.K_ESCAPE:
					return ''
		
		refresh()
		pygame.draw.rect(screen, (25, 25, 25), (lenght, width - 20, 200, 20))
		text = font.render(user_text, True, (255,255,255))
		draw(label, (lenght + 2, width - 10), x_centered = False, y_centered = True)
		draw(text, (lenght + 10, width - 10), x_centered = False, y_centered = True)
		
		pygame.display.flip()

def login():
	global Name
	menu = True
	ok = False
	entries = []
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2) - 60), 120, 40), (255, 255, 255), "Username"))
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2)), 120, 40), (255, 255, 255), "Password"))
	
	buttons = []
	buttons.append(Button((int((lenght + 200) / 2), int((width / 2) + 60), 120, 40), "login_send", "Log in", (0, 255, 0)))
	
	while menu == True:
		char = ''

		mouse_pos = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menu = False
				
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_BACKSPACE:
					char = "\b"
				else:
					if event.key != pygame.K_RETURN:
						char = event.unicode

			if event.type == pygame.MOUSEBUTTONDOWN:
				for elt in entries:
					elt.on_click(mouse_pos)
					
				for elt in buttons:
					if elt.on_click(mouse_pos, f"('{username}', '{password}')") == True:
						Name = username
						menu = False
						return ""

		screen.fill(0)
		
		username = entries[0].show(char)
		password = entries[1].show(char)
		
		for elt in buttons:
			elt.show()
	
		pygame.display.flip()
		
def login_send(username, password):
	global user_data
	server.send(bytes(str(["@Login", username, password]), "utf-8"))
	while True:
		message = menu_listen()
		if len(message) > 0:
			if message[0] == "@Login":
				if message[1] == True:
					user_data = message[2]
					return ""
				if message[1] == False:
					return message[2]

def signin():
	global Name
	menu = True
	entries = []
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2) - 90), 120, 40), (255, 255, 255), "Username"))
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2) - 30), 120, 40), (255, 255, 255), "Password"))
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2) + 30), 120, 40), (255, 255, 255), "Confirm Password"))
	
	buttons = []
	buttons.append(Button((int((lenght + 200) / 2), int((width / 2) + 90), 120, 40), "signin_send", "Sign in", (0, 255, 0)))
	
	while menu == True:
		char = ''

		mouse_pos = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menu = False
				
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_BACKSPACE:
					char = "\b"
				else:
					if event.key != pygame.K_RETURN:
						char = event.unicode

			if event.type == pygame.MOUSEBUTTONDOWN:
				for elt in entries:
					elt.on_click(mouse_pos)
					
				for elt in buttons:
					if elt.on_click(mouse_pos, f"('{username}', '{password}', '{confirm}')") == True:
						Name = username
						menu = False
						return ""

		screen.fill(0)
		
		username = entries[0].show(char)
		password = entries[1].show(char)
		confirm = entries[2].show(char)
		
		for elt in buttons:
			elt.show()
	
		pygame.display.flip()

def signin_send(username, password, confirm):
	global user_data
	if password != confirm:
		return "Passwords must match !"
	elif len(username) == 0 or len(password) == 0:
		return "Passwords or name can't be empty !"
	else:
		server.send(bytes(str(["@Signin", username, password]), "utf-8"))
		while True:
			message = menu_listen()
			if len(message) > 0:
				if message[0] == "@Signin":
					if message[1] == True:
						user_data = message[2]
						return ""
					if message[1] == False:
						return "Name already taken !"

def menu_listen():
	sockets_list = [sys.stdin, server]
	read_sockets, write_socket, error_socket = select.select(sockets_list,[],[])

	for socks in read_sockets:
		if socks == server:
			try:
				msgs = separate(socks.recv(2048).decode())
			except:
				print("Connexion interrompue")

			for msg in msgs:
				if msg[0] == "[" and msg[-1] == "]":
					return eval(msg)

def launch():
	global Name
	players[Name] = Player(Name, [int(lenght / 2), int(width / 2)], 40, "bottom", Skin, "hand", "hand_care", 0)
	server.send(bytes("['@Play']", "utf-8"))
	_thread.start_new_thread(listen, ())
	score = game()
	server.send(bytes(str(["@User", Name, 'score', score]), "utf-8"))
	return score

def clicked():
	return ""

def user_menu():
	global user_data, Skin
	menu = True
	buttons = []
	buttons.append(Button((int((lenght + 200) / 2), int((width / 2) + 40), 120, 40), "clicked", "Play", (0, 255, 0)))
	entries = []
	entries.append(Entry((int((lenght + 200) / 2), int((width / 2) - 40), 120, 40), (255, 255, 255), "Skin"))

	while menu == True:
		char = ''
		
		mouse_pos = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menu = False
				
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_BACKSPACE:
					char = "\b"
				else:
					if event.key != pygame.K_RETURN:
						char = event.unicode
				
			if event.type == pygame.MOUSEBUTTONDOWN:
				for elt in entries:
					elt.on_click(mouse_pos)
				
				for elt in buttons:
					if elt.on_click(mouse_pos, "()") == True:
						score = launch()
						user_data['score'] += score
					
		screen.fill(0)
		screen.blit(font.render(str(user_data["score"]), True, (255, 255, 255)), (10, 10))
		
		for elt in buttons:
			elt.show()
			
		Skin = "player_" + entries[0].show(char)
		
		pygame.display.flip()

def menu():
	menu = True
	buttons = []
	buttons.append(Button((int((lenght + 200) / 2), int((width / 2) - 40), 120, 40), "login", "Log in", (0, 255, 0)))
	buttons.append(Button((int((lenght + 200) / 2), int((width / 2) + 40), 120, 40), "signin", "Sign in", (0, 255, 0)))

	while menu == True:
		mouse_pos = pygame.mouse.get_pos()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				menu = False
		
			if event.type == pygame.MOUSEBUTTONDOWN:
				for elt in buttons:
					if elt.on_click(mouse_pos, "()") == True:
						user_menu()

		screen.fill(0)
		
		for elt in buttons:
			elt.show()
		
		pygame.display.flip()

menu()

server.send(bytes(str(["@Quit", Name]), "utf-8"))
server.close()
