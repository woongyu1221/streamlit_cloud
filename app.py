import streamlit as st
import time
from game_server import GameServer

st.set_page_config(page_title="Streamlit Omok", layout="wide")

# --- Custom CSS for Board ---
st.markdown("""
<style>
    .stButton button {
        width: 30px !important;
        height: 30px !important;
        padding: 0 !important;
        min-height: 0px !important;
        line-height: 0 !important;
        border-radius: 50%;
    }
    div[data-testid="column"] {
        width: 30px !important;
        flex: 0 0 30px !important;
        min-width: 30px !important;
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
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

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
    st.title(f"Lobby - Welcome, {st.session_state.nickname}")
    
    st.subheader("Create a Room")
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
            col1, col2, col3 = st.columns([3, 3, 2])
            with col1:
                st.write(f"**{room.name}**")
            with col2:
                p1 = room.players[1] if room.players[1] else "Waiting..."
                p2 = room.players[2] if room.players[2] else "Waiting..."
                st.write(f"{p1} vs {p2}")
            with col3:
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

    # Sidebar Info
    with st.sidebar:
        st.title(f"Room: {room.name}")
        st.write("---")
        st.write("⚫ Player 1 (Black):")
        st.info(room.players[1] if room.players[1] else "Waiting...")
        
        st.write("⚪ Player 2 (White):")
        st.info(room.players[2] if room.players[2] else "Waiting...")
        
        st.write("---")
        
        # Turn Indicator
        if room.game.winner:
            winner_name = room.players[room.game.winner]
            st.success(f"🏆 Winner: {winner_name}!")
        else:
            current_turn = "⚫ Black's Turn" if room.game.current_turn == 1 else "⚪ White's Turn"
            st.warning(current_turn)
            
        if st.button("Refresh Board"):
            st.rerun()
            
        if st.button("Leave Room"):
            room.leave(st.session_state.nickname)
            st.session_state.room_id = None
            st.rerun()

    # Board Rendering
    # Using columns for grid is heavy but standard API compatible
    game = room.game
    
    # Determine if it's my turn
    my_role = None
    if st.session_state.nickname == room.players[1]:
        my_role = 1
    elif st.session_state.nickname == room.players[2]:
        my_role = 2
        
    is_my_turn = (my_role == game.current_turn) and (not game.winner)
    
    board_container = st.container()
    
    with board_container:
        for r in range(game.size):
            cols = st.columns(game.size, gap="small")
            for c in range(game.size):
                cell_value = game.board[r, c]
                label = " "
                if cell_value == 1:
                    label = "⚫"
                elif cell_value == 2:
                    label = "⚪"
                
                # Check if click should be disabled
                # Disabled if: already occupied OR not my turn OR game over
                occupied = (cell_value != 0)
                disabled = occupied or (not is_my_turn) or (game.winner is not None)
                
                # If button is clicked
                key = f"cell_{r}_{c}"
                if cols[c].button(label, key=key, disabled=disabled):
                    if is_my_turn:
                        success, msg = game.place_stone(r, c)
                        if success:
                            st.rerun()
                        else:
                            st.error(msg)
                            
# --- Main Logic ---
if not st.session_state.nickname:
    login_page()
elif not st.session_state.room_id:
    lobby_page()
else:
    game_page()
