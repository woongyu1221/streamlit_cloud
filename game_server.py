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
        # request format: {'type': 'UNDO'|'SWAP', 'requester': nickname}
        self.pending_request = None
    
    def join(self, player_name):
        # Check if already in the room (Reconnect/Refresh)
        if self.players[1] == player_name:
            return True, "Reconnected as Black"
        if self.players[2] == player_name:
            return True, "Reconnected as White"
        if player_name in self.spectators:
            return True, "Reconnected as Spectator"

        # New Joiner
        if self.players[2] is None:
            self.players[2] = player_name
            return True, "Joined as White"
        else:
            self.spectators.append(player_name)
            return True, "Joined as Spectator"
            
    def leave(self, player_name):
        winner = None
        if self.players[1] == player_name:
            self.players[1] = None
            if self.game.history and not self.game.winner:
                # Player 1 left mid-game -> Player 2 wins
                if self.players[2]:
                    self.game.winner = 2
        elif self.players[2] == player_name:
            self.players[2] = None
            if self.game.history and not self.game.winner:
                # Player 2 left mid-game -> Player 1 wins
                if self.players[1]:
                    self.game.winner = 1
        elif player_name in self.spectators:
            self.spectators.remove(player_name)
            
    def is_empty(self):
        return self.players[1] is None and self.players[2] is None and not self.spectators
            
    def reset_game(self):
        self.game.reset()
        self.pending_request = None

    def make_request(self, requester, req_type):
        # req_type: 'UNDO' or 'SWAP'
        if self.pending_request:
            return False, "Another request is pending"
            
        # Special Case: Single Player Swap
        if req_type == 'SWAP':
            # Check if opponent is missing
            opponent_missing = (self.players[1] is None) or (self.players[2] is None)
            if opponent_missing:
                self.swap_players()
                return True, "Swapped immediately (Single Player)"

        self.pending_request = {'type': req_type, 'requester': requester}
        return True, "Request sent"

    def cancel_request(self):
        self.pending_request = None

    def resolve_request(self, approved):
        if not self.pending_request:
            return False, "No pending request"
        
        req = self.pending_request
        self.pending_request = None
        
        if not approved:
            return True, "Request rejected"
            
        # Execute Action
        if req['type'] == 'UNDO':
            self.game.undo_move()
            return True, "Undo executed"
        elif req['type'] == 'SWAP':
            self.swap_players()
            return True, "Players swapped"
            
        return False, "Unknown request type"

    def swap_players(self):
        p1 = self.players[1]
        p2 = self.players[2]
        self.players[1] = p2
        self.players[2] = p1
        self.game.reset() # Reset game on swap usually makes sense


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
