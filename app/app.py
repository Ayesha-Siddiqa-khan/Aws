from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tictactoe-secret-key")


def check_winner(board):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6],
    ]
    for combo in wins:
        a, b, c = combo
        if board[a] and board[a] == board[b] == board[c]:
            return board[a], combo
    return None, None


def minimax(board, is_maximizing):
    winner, _ = check_winner(board)
    if winner == "O":
        return 10
    if winner == "X":
        return -10
    if all(cell != "" for cell in board):
        return 0
    if is_maximizing:
        best = -1000
        for i in range(9):
            if board[i] == "":
                board[i] = "O"
                best = max(best, minimax(board, False))
                board[i] = ""
        return best
    else:
        best = 1000
        for i in range(9):
            if board[i] == "":
                board[i] = "X"
                best = min(best, minimax(board, True))
                board[i] = ""
        return best


def best_move(board):
    best_val = -1000
    move = -1
    for i in range(9):
        if board[i] == "":
            board[i] = "O"
            val = minimax(board, False)
            board[i] = ""
            if val > best_val:
                best_val = val
                move = i
    return move


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/new-game", methods=["POST"])
def new_game():
    """Return a fresh game state — no server session needed."""
    return jsonify({
        "board": [""] * 9,
        "current_player": "X",
        "game_over": False,
        "winner": None,
        "winning_combo": [],
        "draw": False
    })


@app.route("/api/move", methods=["POST"])
def move():
    """
    Stateless move endpoint.
    Client sends full board + current_player + mode.
    Server validates, applies move, returns new state.
    """
    data = request.get_json()
    board = data.get("board", [""] * 9)
    current_player = data.get("current_player", "X")
    mode = data.get("mode", "pvp")
    index = data.get("index")

    # Validate
    if index is None or index < 0 or index > 8:
        return jsonify({"error": "Invalid index"}), 400
    if board[index] != "":
        return jsonify({"error": "Cell already taken"}), 400

    # Apply player move
    board[index] = current_player
    winner, winning_combo = check_winner(board)

    if winner:
        return jsonify({
            "board": board, "winner": winner,
            "winning_combo": winning_combo,
            "draw": False, "game_over": True,
            "current_player": current_player
        })

    if all(cell != "" for cell in board):
        return jsonify({
            "board": board, "winner": None,
            "winning_combo": [], "draw": True,
            "game_over": True, "current_player": current_player
        })

    next_player = "O" if current_player == "X" else "X"

    # AI move (vs CPU mode)
    if mode == "pvc" and next_player == "O":
        ai_index = best_move(board)
        board[ai_index] = "O"
        winner, winning_combo = check_winner(board)

        if winner:
            return jsonify({
                "board": board, "winner": winner,
                "winning_combo": winning_combo,
                "draw": False, "game_over": True,
                "ai_move": ai_index, "current_player": "O"
            })

        if all(cell != "" for cell in board):
            return jsonify({
                "board": board, "winner": None,
                "winning_combo": [], "draw": True,
                "game_over": True, "ai_move": ai_index,
                "current_player": "O"
            })

        return jsonify({
            "board": board, "winner": None,
            "winning_combo": [], "draw": False,
            "game_over": False, "ai_move": ai_index,
            "current_player": "X"
        })

    return jsonify({
        "board": board, "winner": None,
        "winning_combo": [], "draw": False,
        "game_over": False, "current_player": next_player
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
#