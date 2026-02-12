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
            
        # Check 3-3 Forbidden Move for Black (Player 1)
        if self.current_turn == 1:
            if self.check_forbidden_33(row, col):
                return False, "🚫 Forbidden Move (3-3)"
            
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

    def check_forbidden_33(self, row, col):
        # Simulate placing the stone
        self.board[row, col] = 1
        open_three_count = 0
        
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal \
            (1, -1)   # Diagonal /
        ]
        
        for dr, dc in directions:
            if self.is_open_three(row, col, dr, dc):
                open_three_count += 1
                
        # Undo simulation
        self.board[row, col] = 0
        
        return open_three_count >= 2

    def is_open_three(self, r, c, dr, dc):
        # Check for pattern 0 1 1 1 0 involving the new stone at (r,c)
        # We need to find the continuous line of stones including (r,c)
        
        count = 1
        # Forward
        fr, fc = r + dr, c + dc
        while 0 <= fr < self.size and 0 <= fc < self.size and self.board[fr, fc] == 1:
            count += 1
            fr += dr
            fc += dc
            
        # Backward
        br, bc = r - dr, c - dc
        while 0 <= br < self.size and 0 <= bc < self.size and self.board[br, bc] == 1:
            count += 1
            br -= dr
            bc -= dc
            
        # Strictly open 3 means count == 3 AND both ends are empty (0)
        # Ends are at (fr, fc) and (br, bc)
        if count == 3:
            # Check bounds for ends
            valid_f = (0 <= fr < self.size and 0 <= fc < self.size and self.board[fr, fc] == 0)
            valid_b = (0 <= br < self.size and 0 <= bc < self.size and self.board[br, bc] == 0)
            if valid_f and valid_b:
                return True
                
        return False

    def reset(self):
        self.board = np.zeros((self.size, self.size), dtype=int)
        self.history = []
        self.winner = None
        self.current_turn = 1
