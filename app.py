import streamlit as st
import time
from game_server import GameServer

st.set_page_config(page_title="Streamlit Omok", layout="centered") 

# --- Custom CSS for Board ---
st.markdown("""
<style>
    /* Center the board */
    .stApp {
        align-items: center;
    }
    
    /* Make buttons square and compact */
    .stButton button {
        width: 35px !important;
        height: 35px !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 0 !important;
        min-height: 0px !important; 
        border: 1px solid #ccc;
        border-radius: 0 !important; /* Log shaped */
        background-color: #eebb55; /* Board color */
        color: transparent;
    }
    
    /* Modify columns handling to minimize gaps */
    div[data-testid="column"] {
        width: 35px !important;
        flex: 0 0 35px !important;
        min-width: 35px !important;
        padding: 0 !important;
        gap: 0 !important;
    }
    
    /* Fix row spacing */
    div[data-testid="stHorizontalBlock"] {
        gap: 0 !important;
    }
    
    /* Responsive tweaks */
    @media (max-width: 600px) {
        .stButton button {
            width: 20px !important;
            height: 20px !important;
        }
        div[data-testid="column"] {
            width: 20px !important;
            flex: 0 0 20px !important;
            min-width: 20px !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# --- Global Server State ---
@st.cache_resource
def get_server():
    return GameServer()

server = get_server()

# --- Session State ---
if 'nickname' not in st.session_state:
    st.session_state.nickname = None
if 'room_id' not in st.session_state:
    st.session_state.room_id = None

# --- Pages ---

def login_page():
    st.title("⚫⚪ Streamlit Omok")
    name = st.text_input("Enter your nickname", key="login_name")
    if st.button("Start"):
        if name:
            st.session_state.nickname = name
            st.rerun()
        else:
            st.error("Please enter a nickname.")

def lobby_page():
    st.title(f"Lobby")
    st.caption(f"Logged in as: {st.session_state.nickname}")
    
    with st.expander("Create a Room", expanded=True):
        with st.form("create_room_form"):
            room_name = st.text_input("Room Name")
            submitted = st.form_submit_button("Create")
            if submitted and room_name:
                room_id = server.create_room(room_name, st.session_state.nickname)
                st.session_state.room_id = room_id
                st.success(f"Created room: {room_name}")
                st.rerun()

    st.subheader("Available Rooms")
    rooms = server.get_all_rooms()
    if not rooms:
        st.info("No rooms available. Create one!")
    else:
        for room in rooms:
            cols = st.columns([4, 4, 2])
            with cols[0]:
                st.write(f"**{room.name}**")
            with cols[1]:
                p1 = room.players[1] if room.players[1] else "-"
                p2 = room.players[2] if room.players[2] else "-"
                st.caption(f"{p1} vs {p2}")
            with cols[2]:
                if st.button("Join", key=f"join_{room.id}"):
                    success, msg = room.join(st.session_state.nickname)
                    if success:
                        st.session_state.room_id = room.id
                        st.rerun()
                    else:
                        st.error(msg)
    
    if st.button("Refresh Lobby"):
        st.rerun()

def game_page():
    room = server.get_room(st.session_state.room_id)
    if not room:
        st.error("Room not found or expired.")
        time.sleep(2)
        st.session_state.room_id = None
        st.rerun()
        return

    game = room.game
    
    # Identify Player
    my_role = None
    if st.session_state.nickname == room.players[1]:
        my_role = 1 # Black
    elif st.session_state.nickname == room.players[2]:
        my_role = 2 # White
    else:
        my_role = 0 # Spectator

    # Sidebar: Game Info & Controls
    with st.sidebar:
        st.header(f"Room: {room.name}")
        
        # Player Status
        p1_name = room.players[1] if room.players[1] else "Waiting..."
        p2_name = room.players[2] if room.players[2] else "Waiting..."
        
        st.markdown(f"**Unknown Player (Black)**: {p1_name}")
        st.markdown(f"**White Player (White)**: {p2_name}")
        
        st.divider()
        
        # Turn / Game Status
        ready_to_play = (room.players[1] is not None) and (room.players[2] is not None)
        
        if my_role == 0:
            st.info("👀 You are a Spectator")
        
        if not ready_to_play:
            st.warning("Waiting for opponent...")
        elif room.game.winner:
            winner_name = room.players[room.game.winner]
            st.success(f"🏆 Winner: {winner_name}!")
        else:
            turn_name = room.players[room.game.current_turn]
            color_icon = "⚫" if room.game.current_turn == 1 else "⚪"
            if room.game.current_turn == my_role:
                st.info(f"{color_icon} YOUR TURN")
            else:
                st.markdown(f"{color_icon} {turn_name}'s turn")

        st.divider()
        
        # Actions
        col_act1, col_act2 = st.columns(2)
        with col_act1:
            if st.button("Refresh"):
                st.rerun()
        with col_act2:
            if st.button("Undo"):
                # Ideally, we should vote to undo, but for now simple undo
                if my_role in [1, 2]: # Only players can undo
                     game.undo_move()
                     st.rerun()
        
        if st.button("Leave Room", type="primary"):
            room.leave(st.session_state.nickname)
            if room.is_empty():
                 server.remove_room(room.id)
            st.session_state.room_id = None
            st.rerun()

    # Board Rendering
    # Use a container to keep it tight
    with st.container():
        for r in range(game.size):
            # Create columns with minimal gap
            cols = st.columns(game.size) 
            for c in range(game.size):
                cell_value = game.board[r, c]
                
                # Visual logic
                label = " "
                if cell_value == 1:
                    label = "⚫" # Black stone
                elif cell_value == 2:
                    label = "⚪" # White stone
                
                # Logic for disabled state
                # 1. Spot occupied?
                # 2. Not my turn?
                # 3. Game finished?
                # 4. Opponent missing?
                # 5. Spectator?
                is_occupied = (cell_value != 0)
                is_game_over = (game.winner is not None)
                is_my_turn = (game.current_turn == my_role)
                is_player = (my_role in [1, 2])
                
                disabled = True
                if is_player and not is_occupied and not is_game_over and ready_to_play and is_my_turn:
                    disabled = False
                
                # We need unique keys for buttons
                key = f"b_{r}_{c}"
                
                # In order to color the stone, we can't easily change button text color in standard Streamlit
                # So we use the emoji label which carries its own color.
                if cols[c].button(label, key=key, disabled=disabled):
                    if not disabled:
                        game.place_stone(r, c)
                        st.rerun()

# --- Main Logic ---
if not st.session_state.nickname:
    login_page()
elif not st.session_state.room_id:
    lobby_page()
else:
    game_page()
