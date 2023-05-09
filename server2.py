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
error = []

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
		list_of_clients.pop(elt)
	error = []

class Player:
	def __init__(self, name, position, life, direction, skin, weapon):
		self.name = name
		self.position = position
		self.life = life
		self.direction = direction
		self.skin = skin
		self.weapon = eval(weapon + "()")

class Client:
	def __init__(self, conn, addr):
		self.conn = conn
		self.addr = addr
		_thread.start_new_thread(self.listen, ())
		self.conn.send(bytes("['@Welcome']", "utf-8"))

	def listen(self):
		while True:
			try:
				msg = self.conn.recv(2048).decode()
			except:
				print("Connexion reset by " + addr[0])
				self.delete(addr[0])

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
					
					elif evaluate_msg[0] == "@Player":
						for key in list(players.keys()):
							self.conn.send(bytes(str(['@Player', players[key].name, players[key].position, players[key].life, players[key].direction, players[key].skin, players[key].weapon.name]), "utf-8"))
						players[evaluate_msg[1]] = Player(evaluate_msg[1], evaluate_msg[2], evaluate_msg[3], evaluate_msg[4], evaluate_msg[5], evaluate_msg[6])
						self.conn.send(bytes("['@Go']", "utf-8"))
						self.name = evaluate_msg[1]
					
					elif evaluate_msg[0] == "@Leave":
						self.delete(evaluate_msg[1])
						
	def delete(self, name):
		try:
			del(players[name])
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
		broadcast(f"['@Box', {nb}, {[random.randint(4, (lenght-32) // 10), random.randint(4, (width-32) // 10)]}, {time.time() + 10}, '{choose(items)}']", 0)
		nb += 1
		
def zone_spawn():
	while True:
		time.sleep(60)
		broadcast(f"['@Zone', {[random.randint(4, (lenght-32) // 10), random.randint(4, (width-32) // 10)]}, {time.time() + 60}]", 0)

_thread.start_new_thread(box_spawn, ())
_thread.start_new_thread(zone_spawn, ())

run = True
while run:
	conn, addr = server.accept()
	list_of_clients.append(Client(conn, addr))
	print(addr[0], "is connected")

server.close()
