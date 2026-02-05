import numpy as np

class OmokGame:
    def __init__(self, size=15):
        self.size = size
        self.board = np.zeros((size, size), dtype=int)
        self.history = []
        self.winner = None
        self.current_turn = 1  # 1: Black, 2: White

    def place_stone(self, row, col):
        if self.winner is not None:
            return False, "Game already finished"
        
        if not (0 <= row < self.size and 0 <= col < self.size):
            return False, "Invalid position"
            
        if self.board[row, col] != 0:
            return False, "Position already taken"
            
        self.board[row, col] = self.current_turn
        self.history.append((row, col, self.current_turn))
        
        if self.check_winner(row, col):
            self.winner = self.current_turn
        else:
            self.current_turn = 3 - self.current_turn  # Switch 1 <-> 2
            
        return True, "Stone placed"

    def check_winner(self, last_r, last_c):
        player = self.board[last_r, last_c]
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal \
            (1, -1)   # Diagonal /
        ]
        
        for dr, dc in directions:
            count = 1
            # Check forward
            r, c = last_r + dr, last_c + dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r, c] == player:
                count += 1
                r += dr
                c += dc
            
            # Check backward
            r, c = last_r - dr, last_c - dc
            while 0 <= r < self.size and 0 <= c < self.size and self.board[r, c] == player:
                count += 1
                r -= dr
                c -= dc
                
            if count >= 5:
                return True
                
        return False
        
    def undo_move(self):
        if not self.history:
            return False, "No moves to undo"
            
        last_row, last_col, player = self.history.pop()
        self.board[last_row, last_col] = 0
        self.current_turn = player # Revert turn to the player who made the move
        self.winner = None # Reset winner state if we undo a winning move
        return True, "Last move undone"

    def reset(self):
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.history = []
        self.winner = None
        self.current_turn = 1
