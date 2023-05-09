import socket
import select
import sys
import _thread
import pygame
import time
import random
from common import *

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

if len(sys.argv) != 3:
	print("Correct usage: IP, Port")
	
server.connect((str(sys.argv[1]), int(sys.argv[2])))

Name = input("entrez votre nom: ")
Skin = input("entrez votre skin: ")

global players, boxes, messages, fps
players = {}
boxes = {}
messages = []

def draw(image, xy, centered = True):
	if centered == True:
		pos = image.get_rect()
		pos.center = xy
	else:
		pos = xy
	screen.blit(image, pos)

class Player:
	def __init__(self, name, position, life, direction, skin, weapon):
		self.name = name
		self.position = position
		self.life = life
		self.direction = direction
		self.dead = False
		self.skin = skin
		self.weapon = eval(weapon + "()")
		self.respawn_time = 0
		self.trace_time = 0
		self.hurted_time = 0
		self.texture = pygame.image.load(f".PyCombat/textures/{self.skin}/{self.direction}.png").convert_alpha()
		self.show()

	def show(self):
		if self.dead == False:
			if self.hurted_time > time.time():
				rand_x = random.randint(-2, 2)
				rand_y = random.randint(-2, 2)
				
				screen.blit(self.texture, (self.position[0] - 16 + rand_x, self.position[1] - 16 + rand_y))
				draw(font.render(self.name, True, (255,255,255)), (self.position[0] + rand_y, self.position[1] - 32 + rand_x))
				pygame.draw.line(screen, (255, 0, 0), (self.position[0] - 20 + rand_y, self.position[1] - 22 + rand_x), (int(self.position[0] - 20 + self.life + rand_x), self.position[1] - 22 + rand_y), 4)
			else:
				draw(font.render(self.name, True, (255,255,255)), (self.position[0], self.position[1] - 32))
				pygame.draw.line(screen, (255, 0, 0), (self.position[0] - 20, self.position[1] - 22), (int(self.position[0] - 20 + self.life), self.position[1] - 22), 4)
				screen.blit(self.texture, (self.position[0] - 16, self.position[1] - 16))

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
			
		if self.dead == True:
			if self.respawn_time - 4.7 >= time.time():
				pygame.draw.line(screen, (235, 235, 255), (self.position[0], 0), (self.position[0] + 30, self.position[1] // 3), 6)
				pygame.draw.line(screen, (235, 235, 255), (self.position[0] + 30, self.position[1] // 3), (self.position[0] - 30, self.position[1] * 2 // 3), 5)
				pygame.draw.line(screen, (235, 235, 255), (self.position[0] - 30, self.position[1] * 2 // 3), (self.position[0], self.position[1]), 4)
			if self.name == Name:
				draw(font3.render("Respawn in " + str(int(self.respawn_time - time.time())), True, (255,255,255)), (lenght // 2, width // 2))
				if self.respawn_time <= time.time():
					self.death(False)

	def move(self, move):
		if self.dead == False:
			self.position[0] += move[0]
			self.position[1] += move[1]
			if move[1] > 0:
				self.direction = "bottom"
			elif move[1] < 0:
				self.direction = "top"
			if move[0] > 0:
				self.direction = "right"
			elif move[0] < 0:
				self.direction = "left"

			self.texture = pygame.image.load(f".PyCombat/textures/{self.skin}/{self.direction}.png").convert_alpha()
			server.send(bytes(str(['@Move', self.name, self.position, self.direction]), "utf-8"))

	def attack(self):
		if self.name == Name:
			if self.dead == False:
				server.send(bytes(str(['@Attack', self.name]), "utf-8"))
				self.weapon.durability -= 1
				if self.weapon.durability == 0:
					self.weapon = hand()
					server.send(bytes(str(['@Weapon', self.name, self.weapon.name]), "utf-8"))

		self.trace_time = time.time() + 0.1
		self.rand_x = random.randint(- 2, 2)
		self.rand_y = random.randint(- 2, 2)

	def hurted(self, weapon, position):
		if abs(position[0] - self.position[0]) < 48 and abs(position[1] - self.position[1]) < 48:
			if self.dead == False:
				self.hurted_time = time.time() + 0.1
				self.life -= weapon.damages
				server.send(bytes(str(['@Life', self.name, self.life]), "utf-8"))
				
				if self.life < 1:
					self.respawn_time = time.time() + 5
					self.death(True)
			
	def death(self, dead):
		self.dead = dead
		if dead == False:
			self.life = 20
			server.send(bytes(str(['@Life', self.name, self.life]), "utf-8"))
		server.send(bytes(str(['@Death', self.name, self.dead]), "utf-8"))
		
	def player(self):
		server.send(bytes(str(["@Player", self.name, self.position, self.life, self.direction, self.skin, self.weapon.name]), "utf-8"))

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
			players[Name].weapon = eval((self.loot + "()"))
			server.send(bytes(str(['@Taken', self.name]), "utf-8"))
			server.send(bytes(str(['@Weapon', players[Name].name, players[Name].weapon.name]), "utf-8"))
			del(boxes[self.name])

def listen(init):
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
							players[Name].hurted(players[evaluate_msg[1]].weapon, players[evaluate_msg[1]].position)
							players[evaluate_msg[1]].attack()

						elif evaluate_msg[0] == "@Life":
							players[evaluate_msg[1]].life = evaluate_msg[2]
							players[evaluate_msg[1]].hurted_time = time.time() + 0.1
							
						elif evaluate_msg[0] == "@Death":
							players[evaluate_msg[1]].dead = evaluate_msg[2]
							players[evaluate_msg[1]].respawn_time = time.time() + 5
						
						elif evaluate_msg[0] == "@Box":
							boxes[evaluate_msg[1]] = Box(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4])
							
						elif evaluate_msg[0] == "@Taken":
							try:
								del(boxes[evaluate_msg[1]])
							except:
								pass
							
						elif evaluate_msg[0] == "@Weapon":
							players[evaluate_msg[1]].weapon = eval(evaluate_msg[2] + "()")
							
						
						elif evaluate_msg[0] == "@Message":
							messages.append(evaluate_msg[1])
							
						elif evaluate_msg[0] == "@Leave":
							try:
								del(players[evaluate_msg[1]])
								print("Player named " + evaluate_msg[1] + " has been deleted")
							except:
								print("Player named " + evaluate_msg[1] + " is already deleted")
						
					if evaluate_msg[0] == "@Player":
						players[evaluate_msg[1]] = Player(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4], evaluate_msg[5], evaluate_msg[6])

pygame.init()
screen = pygame.display.set_mode((lenght + 200, width))
pygame.display.set_caption("Combat")

font = pygame.font.Font(".PyCombat/LiberationMono-Bold.ttf", 10)
font3 = pygame.font.Font(".PyCombat/LiberationMono-Bold.ttf", 30)

pygame.key.set_repeat(1, 30)

def refresh():
	screen.fill(0)
	for i in range(len(messages)):
		screen.blit(font.render(messages[i], True, (255,255,255)), (lenght, i * 15))
	try:
		for elt in list(boxes.keys()):
			boxes[elt].show()
	except:
		pass

	for i in range(len(players.keys()) - 1, -1, -1):
		players[list(players.keys())[i]].show()

	screen.blit(font.render(str(fps), True, (255,255,255)), (10, 10))
	screen.blit(font.render(players[Name].weapon.name, True, (255,255,255)), (10, 20))

def chat():
	label = font.render(":", True, (255,255,255))
	user_text = ''
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_BACKSPACE:
					user_text = user_text[:-1]

				else:
					user_text += event.unicode
					
				if event.key == pygame.K_RETURN:
					server.send(bytes(str(["@Message", "<" + Name + "> " + user_text[:-1]]), "utf-8"))
					messages.append("<" + Name + "> " + user_text[:-1])
					user_text =''
					
				if event.key == pygame.K_ESCAPE:
					return ''
		
		refresh()
		pygame.draw.rect(screen, (25, 25, 25), (lenght, width - 20, 200, 20))
		text = font.render(user_text, True, (255,255,255))
		screen.blit(label, (lenght + 2, width - 20))
		screen.blit(text, (lenght + 10, width - 20))
		
		pygame.display.update()
		time.sleep(0.2)

def menu():
	players[Name] = Player(Name, [int(lenght / 2), int(width / 2)], 40, "bottom", Skin, "hand")
	_thread.start_new_thread(listen, (True,))
	game()

def game():
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
				players[Name].attack()
				for elt in list(boxes.keys()):
					boxes[elt].hurted(players[Name].position)
				
		if move[0] != 0 or move[1] != 0:
			players[Name].move(move)
		refresh()
		pygame.display.update()
		fps_now += 1

menu()

server.send(bytes(str(["@Leave", Name]), "utf-8"))
server.close()
