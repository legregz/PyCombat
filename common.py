lenght = 500
width = 500

def separate(msg):
	msgs = []
	start = 0
	for i in range(len(msg) - 2):
		if msg[i:i+2] == "][":
			msgs.append(msg[start:i+1])
			start = i + 1
		elif i == len(msg) - 3:
			msgs.append(msg[start:i + 3])
			start = i + 1
	return msgs
	
class Weapon:
	def __init__(self, name, damages, trace, durability, probability = 1):
		self.name = name
		self.trace = trace
		self.damages = damages
		self.durability = durability
		self.probability = probability

def knife():
	return Weapon('knife', 1, "middle_trace", 8, 2)
	
def hand():
	return Weapon('hand', 0.5, "little_trace", 1000)
	
def sword():
	return Weapon('sword', 2, "big_trace", 5, 1)
	
items = ["knife", "sword"]
