import os
import re
import json

BOARD_FILE = "board.txt"
README_FILE = "README.md"

def read_board():
    with open(BOARD_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    board = lines[:8]
    next_player = lines[-1].split(":")[1].strip()
    return board, next_player

def write_board(board, next_player):
    with open(BOARD_FILE, "w", encoding="utf-8") as f:
        for row in board:
            f.write(row + "\n")
        f.write(f"\nNext: {next_player}\n")

def parse_move():
    # Baca data dari event GitHub
    with open(os.environ['GITHUB_EVENT_PATH'], 'r', encoding='utf-8') as f:
        event = json.load(f)

    title = event["issue"]["title"]
    match = re.search(r"[Mm]ove:\s*([A-Ha-h][1-8])", title)

    if not match:
        raise ValueError("Format judul harus seperti: 'move: D3'")

    move = match.group(1).upper()
    col = ord(move[0]) - ord('A')
    row = 8 - int(move[1])

    if not (0 <= row < 8 and 0 <= col < 8):
        raise ValueError("Koordinat move berada di luar papan (A1 - H8).")

    return row, col

def apply_move(board, row, col, player):
    if board[row][col] != ".":
        raise ValueError(f"Sel {chr(col + ord('A'))}{8 - row} sudah terisi.")

    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    to_flip = []
    opponent = "W" if player == "B" else "B"
    for dr, dc in directions:
        r, c = row + dr, col + dc
        tmp = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            tmp.append((r, c))
            r += dr
            c += dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player and tmp:
            to_flip.extend(tmp)

    if not to_flip:
        raise ValueError("Move tidak valid: tidak ada keping lawan yang bisa dibalik.")

    board[row] = board[row][:col] + player + board[row][col+1:]
    for r, c in to_flip:
        board[r] = board[r][:c] + player + board[r][c+1:]
    return board

def switch_player(player):
    return "W" if player == "B" else "B"

def generate_game_md(board, next_player):
    md = f"✅ **Next player: {'⚫ Black' if next_player == 'B' else '⚪ White'}**\n"
    md += "🟩 **Current Board**\n\n"

    md += "|   | A | B | C | D | E | F | G | H |\n"
    md += "|---|---|---|---|---|---|---|---|---|\n"

    emoji_map = {
        ".": " ",
        "B": "⚫",
        "W": "⚪"
    }

    for row in range(8):
        md += f"| {8 - row} "
        for col in range(8):
            cell = board[row][col]
            md += f"| {emoji_map.get(cell, ' ')} "
        md += "|\n"
    return md

def render_readme(board, next_player):
    with open(README_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    game_md = generate_game_md(board, next_player)

    new_content = re.sub(
        r"<!-- GAME-START -->.*?<!-- GAME-END -->",
        f"<!-- GAME-START -->\n{game_md}\n<!-- GAME-END -->",
        content,
        flags=re.DOTALL
    )

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(new_content)

if __name__ == "__main__":
    try:
        board, next_player = read_board()
        move_row, move_col = parse_move()
        board = apply_move(board, move_row, move_col, next_player)
        next_player = switch_player(next_player)
        write_board(board, next_player)
        render_readme(board, next_player)
    except Exception as e:
        print(f"::error::{e}")
        exit(1)
