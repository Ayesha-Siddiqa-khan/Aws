from flask import Flask, render_template, jsonify, request, session
import os
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "tictactoe-secret-key")


def check_winner(board):
    wins = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [2, 4, 6],              # diagonals
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
    data = request.get_json()
    mode = data.get("mode", "pvp")  # pvp or pvc
    session["board"] = [""] * 9
    session["current_player"] = "X"
    session["mode"] = mode
    session["game_over"] = False
    return jsonify({"board": session["board"], "current_player": "X", "mode": mode})


@app.route("/api/move", methods=["POST"])
def move():
    data = request.get_json()
    index = data.get("index")
    board = session.get("board", [""] * 9)
    current_player = session.get("current_player", "X")
    mode = session.get("mode", "pvp")
    game_over = session.get("game_over", False)

    if game_over or board[index] != "" or index is None:
        return jsonify({"error": "Invalid move"}), 400

    board[index] = current_player
    winner, winning_combo = check_winner(board)

    if winner:
        session["board"] = board
        session["game_over"] = True
        return jsonify({"board": board, "winner": winner, "winning_combo": winning_combo, "draw": False})

    if all(cell != "" for cell in board):
        session["board"] = board
        session["game_over"] = True
        return jsonify({"board": board, "winner": None, "winning_combo": None, "draw": True})

    next_player = "O" if current_player == "X" else "X"
    session["current_player"] = next_player
    session["board"] = board

    # AI move
    if mode == "pvc" and next_player == "O":
        ai_index = best_move(board)
        board[ai_index] = "O"
        winner, winning_combo = check_winner(board)
        session["board"] = board

        if winner:
            session["game_over"] = True
            return jsonify({"board": board, "winner": winner, "winning_combo": winning_combo, "draw": False, "ai_move": ai_index})

        if all(cell != "" for cell in board):
            session["game_over"] = True
            return jsonify({"board": board, "winner": None, "winning_combo": None, "draw": True, "ai_move": ai_index})

        session["current_player"] = "X"
        return jsonify({"board": board, "winner": None, "winning_combo": None, "draw": False, "ai_move": ai_index, "current_player": "X"})

    return jsonify({"board": board, "winner": None, "winning_combo": None, "draw": False, "current_player": next_player})


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
