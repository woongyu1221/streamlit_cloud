import uuid
from game_logic import OmokGame

class Room:
    def __init__(self, room_name, creator_name):
        self.id = str(uuid.uuid4())
        self.name = room_name
        self.game = OmokGame()
        self.players = {
            1: creator_name, # Black
            2: None          # White
        }
        self.spectators = []
    
    def join(self, player_name):
        if self.players[2] is None:
            self.players[2] = player_name
            return True, "Joined as White"
        else:
            self.spectators.append(player_name)
            return True, "Joined as Spectator"
            
    def leave(self, player_name):
        if self.players[1] == player_name:
            self.players[1] = None
        elif self.players[2] == player_name:
            self.players[2] = None
        elif player_name in self.spectators:
            self.spectators.remove(player_name)
            
    def is_empty(self):
        return self.players[1] is None and self.players[2] is None and not self.spectators
            
    def reset_game(self):
        self.game.reset()

class GameServer:
    def __init__(self):
        self.rooms = {} # room_id -> Room

    def create_room(self, room_name, creator_name):
        new_room = Room(room_name, creator_name)
        self.rooms[new_room.id] = new_room
        return new_room.id

    def get_room(self, room_id):
        return self.rooms.get(room_id)
        
    def remove_room(self, room_id):
        if room_id in self.rooms:
            del self.rooms[room_id]

    def get_all_rooms(self):
        return list(self.rooms.values())
