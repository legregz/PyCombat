import socket
import select
import sys
import _thread
import time
from common import *
import random

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if len(sys.argv) == 3:
	server.bind((str(sys.argv[1]), int(sys.argv[2])))
	print(f"Server started on {sys.argv[1]} with port {sys.argv[2]}")
else:
	server.bind(("0.0.0.0", 55352))
	print("Server started on 0.0.0.0 with port 55352")

server.listen(10)

list_of_clients = []
players = {}
zones = {}
boxes = {}
error = []
end = 0

def broadcast(msg, addr):
	global error
	for i in range(len(list_of_clients)):
		if list_of_clients[i].addr != addr:
			try:
				list_of_clients[i].conn.send(bytes(msg, "utf-8"))
			except:
				print("Impossible to send to", list_of_clients[i].addr[0])
				try:
					broadcast(f"['@Leave', '{list_of_clients[i].name}']", list_of_clients[i].addr)
				except:
					pass
				error.append(i)
	for elt in error:
		try:
			list_of_clients[elt].delete(list_of_clients[elt].addr[0])
		except:
			print("player already deleted")
		try:
			del(list_of_clients[elt])
		except:
			print("Client alread deleted")
	error = []

class Box:
	def __init__(self, name, position, end, loot):
		self.name = name
		self.position = position
		self.end = end
		self.loot = loot
		
class Zone:
	def __init__(self, name, position, end):
		self.name = name
		self.position = position
		self.end = end

class Player:
	def __init__(self, name, position, life, direction, skin, weapon, care, score):
		self.name = name
		self.position = position
		self.life = life
		self.direction = direction
		self.skin = skin
		self.weapon = eval(weapon + "()")
		self.care = eval(care + "()")
		self.score = score

class Client:
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		_thread.start_new_thread(self.listen, ())

	def listen(self):
		while True:
			try:
				msg = self.conn.recv(2048).decode()
			except:
				print("Connexion reset by " + self.addr[0])
				self.delete(self.addr[0])

			if len(msg) > 0:
				msgs = separate(msg)
				for elt in msgs:
					print("<"+ self.addr[0]+"> " + elt)
					broadcast(elt, self.addr)
					
					evaluate_msg = eval(elt)
					
					if evaluate_msg[0] == "@Move":
						players[evaluate_msg[1]].position = evaluate_msg[2]
						players[evaluate_msg[1]].direction = evaluate_msg[3]
					
					elif evaluate_msg[0] == "@Life":
						players[evaluate_msg[1]].life = evaluate_msg[2]
						
					elif evaluate_msg[0] == "@Care":
						players[evaluate_msg[1]].care = evaluate_msg[2]
					
					elif evaluate_msg[0] == "@Player":
						for key in list(players.keys()):
							self.conn.send(bytes(str(['@Player', players[key].name, players[key].position, players[key].life, players[key].direction, players[key].skin, players[key].weapon.name, players[key].care.name, players[key].score]), "utf-8"))
						players[evaluate_msg[1]] = Player(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4], evaluate_msg[5], evaluate_msg[6], evaluate_msg[7], evaluate_msg[8])
						
						for key in list(boxes.keys()):
							self.conn.send(bytes(f"['@Box', {boxes[key].name}, {boxes[key].position}, {boxes[key].end}, '{boxes[key].loot}']", "utf-8"))
							
						for key in list(zones.keys()):
							self.conn.send(bytes(f"['@Zone', {zones[key].name}, {zones[key].position}, {zones[key].end}]", "utf-8"))
							
						self.conn.send(bytes(f"['@Time', {end}]", "utf-8"))
						
						self.conn.send(bytes("['@Go']", "utf-8"))
						self.name = evaluate_msg[1]
					
					elif evaluate_msg[0] == "@Play":
						self.conn.send(bytes("['@Welcome']", "utf-8"))
						
					elif evaluate_msg[0] == "@User":
						file = open(".PyCombat/data.json", "r")
						content = eval(file.read())
						file.close()
						content[evaluate_msg[1]][evaluate_msg[2]] += evaluate_msg[3]
						
						save = False
						while save != True:
							try:
								file = open(".PyCombat/data.json", "w")
								file.write(str(content))
								file.close()
								save = True
							except:
								pass
					
					elif evaluate_msg[0] == "@Login":
						file = open(".PyCombat/data.json", "r")
						content = eval(file.read())
						file.close()

						try:
							data = content[evaluate_msg[1]]
							if data['password'] == hashing(evaluate_msg[2]):
								self.conn.send(bytes(f"['@Login', True, {data}]", "utf-8"))
							else:
								self.conn.send(bytes(f"['@Login', False, 'Invalid password !']", "utf-8"))
						except:
							self.conn.send(bytes(f"['@Login', False, 'Invalid username !']", "utf-8"))
					
					elif evaluate_msg[0] == "@Signin":
						file = open(".PyCombat/data.json", "r")
						content = eval(file.read())
						file.close()
						
						founded = False
						for key in list(content.keys()):
							if key == evaluate_msg[1]:
								founded = True
								self.conn.send(bytes("['@Signin', False]", "utf-8"))
								break
								
						if founded == False:
							data = {"password": hashing(evaluate_msg[2]), "score": 0}
							content[evaluate_msg[1]] = data
							
							save = False
							while save != True:
								try:
									file = open(".PyCombat/data.json", "w")
									file.write(str(content))
									file.close()
									save = True
								except:
									pass
									
							self.conn.send(bytes(f"['@Signin', True, {data}]", "utf-8"))
					
					elif evaluate_msg[0] == "@Quit":
						self.delete(evaluate_msg[1])
						
	def delete(self, name):
		try:
			del(players[self.name])
			print("Player named " + self.name + " is deleted")
		except:
			print("Impossible to delete player called '" + name + "'")
		self.conn.close()
		_thread.exit()

def choose(param):
	items_list = []
	for elt in param:
		for i in range(eval(elt + "()").probability):
			items_list.append(elt)
	return items_list[random.randint(0, len(items_list) - 1)]

def box_spawn():
	nb = 0
	while True:
		time.sleep(random.randint(3, 5))
		position = [random.randint(4, (lenght-32) // 10), random.randint(4, (width-32) // 10)]
		end = time.time() + 10
		loot = choose(items)
		broadcast(f"['@Box', {nb}, {position}, {end}, '{loot}']", 0)
		boxes[nb] = Box(nb, position, end, loot)
		nb += 1
		
def del_box():
	while True:
		for key in list(boxes.keys()):
			if boxes[key].end < time.time():
				del(boxes[key])
		
def zone_spawn():
	while True:
		position = [random.randint(4, (lenght-32) // 10), random.randint(4, (width-32) // 10)]
		end = time.time() + 20
		broadcast(f"['@Zone', 1, {position}, {end}]", 0)
		zones[1] = Zone(1, position, end)
		time.sleep(20)
		
def game():
	global end, players
	while True:
		end = time.time() + 60
		time.sleep(60)
		broadcast(f"['@End']", 0)
		players = {}

_thread.start_new_thread(box_spawn, ())
_thread.start_new_thread(zone_spawn, ())
_thread.start_new_thread(del_box, ())
_thread.start_new_thread(game, ())

run = True
while run:
	conn, addr = server.accept()
	list_of_clients.append(Client(conn, addr))
	print(addr[0], "is connected")

server.close()
