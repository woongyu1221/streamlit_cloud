import streamlit as st
import time
from game_server import GameServer
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Streamlit Omok", layout="centered") 

# --- Custom CSS for Board ---
# --- Custom CSS for Board ---
st.markdown("""
<style>
    /* Center the board */
    .stApp {
        align-items: center;
    }
    
    /* 
       Target ONLY buttons inside the MAIN area of the Game View.
       We use a marker div #game_view_marker to activate this style.
       This ensures:
       1. It only affects the Game Page (because of the marker).
       2. It only affects the Main Board (because of strict stMain scoping).
       3. Sidebar buttons are UNTOUCHED.
    */
    section[data-testid="stMain"]:has(#game_view_marker) .stButton button {
        width: 35px !important;
        height: 35px !important;
        padding: 0 !important;
        margin: 0 !important;
        line-height: 0 !important;
        min-height: 0px !important; 
        border: 1px solid #c6a35b;
        border-radius: 0 !important; 
        background-color: #eebb55; 
        color: black !important; /* Make text visible (emojis) */
        font-size: 18px;
    }

    /* Modify columns handling to minimize gaps - Only for Board in Main */
    section[data-testid="stMain"]:has(#game_view_marker) div[data-testid="column"] {
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
        
    # Auto-refresh lobby every 5 seconds
    st_autorefresh(interval=5000, limit=None, key="lobby_refresh")

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
            # Refresh every 2s while waiting for opponent
            st_autorefresh(interval=2000, key="wait_player_refresh")
            
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
                # Refresh every 1s if it's NOT my turn (waiting for opponent move)
                st_autorefresh(interval=1000, key="wait_move_refresh")
        
        # Also refresh if there is a pending request for ME to handle
        if room.pending_request and room.pending_request['requester'] != st.session_state.nickname:
             st_autorefresh(interval=2000, key="request_refresh")

        st.divider()
        
        st.divider()
        
        # --- Value-Added Features: Requests ---
        # 1. Check if there is a pending request targeting ME?
        #    Target is the 'other' player.
        pending = room.pending_request
        
        # Logic to determine if I am the resolver (the one receiving the request)
        i_am_resolver = False
        if pending and pending['requester'] != st.session_state.nickname:
             if my_role in [1, 2]: # Spectators don't resolve
                 i_am_resolver = True
        
        if i_am_resolver:
            req_type = pending['type']
            requester = pending['requester']
            st.warning(f"📩 {requester} wants to **{req_type}**.")
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                if st.button("✅ Accept", key="accept_req"):
                    room.resolve_request(True)
                    st.rerun()
            with col_res2:
                if st.button("❌ Deny", key="deny_req"):
                    room.resolve_request(False)
                    st.rerun()
        
        elif pending and pending['requester'] == st.session_state.nickname:
            st.info(f"⏳ Waiting for opponent to accept {pending['type']}...")
            if st.button("Cancel Request"):
                room.cancel_request()
                st.rerun()
                
        else:
            # Normal Controls
            st.write("### Controls")
            col_act1, col_act2 = st.columns(2)
            with col_act1:
                if st.button("🔄 Refresh", help="Refresh the board"):
                    st.rerun()
            with col_act2:
                # UNDO Request
                if st.button("↩️ Undo", help="Request undo", disabled=not (my_role in [1, 2])):
                    room.make_request(st.session_state.nickname, 'UNDO')
                    st.rerun()
            
            # SWAP Request
            if st.button("⇄ Swap / Reset", help="Request to swap seats and restart", disabled=not (my_role in [1, 2])):
                room.make_request(st.session_state.nickname, 'SWAP')
                st.rerun()
            
            if st.button("🚪 Leave Room", type="primary", help="Exit the game"):
                room.leave(st.session_state.nickname)
                if room.is_empty():
                     server.remove_room(room.id)
                st.session_state.room_id = None
                st.rerun()

    # Board Rendering
    # Use a container to keep it tight
    st.markdown('<div id="game_view_marker"></div>', unsafe_allow_html=True)
    
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
                
                # We can't actually disable the button if we want the click to register eventually or tooltip to show
                # But standard disable grey out is fine.
                disabled = True
                if is_player and not is_occupied and not is_game_over and ready_to_play and is_my_turn:
                    disabled = False
                
                # We need unique keys for buttons
                key = f"b_{r}_{c}"
                
                # Button
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
