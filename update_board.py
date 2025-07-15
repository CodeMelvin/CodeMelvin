import re
import subprocess

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
    log = subprocess.check_output(["git", "log", "-1", "--pretty=%B"]).decode()
    match = re.search(r"[Mm]ove:\s*([A-H][1-8])", log)
    if not match:
        raise ValueError("No valid move found in commit message or issue title.")
    col = ord(match.group(1)[0].upper()) - ord("A")
    row = 8 - int(match.group(1)[1])
    return row, col

def apply_move(board, row, col, player):
    if board[row][col] != ".":
        raise ValueError("Cell already occupied.")
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    to_flip = []
    opponent = "W" if player == "B" else "B"
    for dr, dc in directions:
        r, c = row+dr, col+dc
        tmp = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            tmp.append((r,c))
            r += dr
            c += dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player and tmp:
            to_flip.extend(tmp)
    if not to_flip:
        raise ValueError("Invalid move, no pieces to flip.")
    board[row] = board[row][:col] + player + board[row][col+1:]
    for r,c in to_flip:
        board[r] = board[r][:c] + player + board[r][c+1:]
    return board

def switch_player(player):
    return "W" if player == "B" else "B"

def generate_game_md(board, next_player):
    md = f"✅ **Next player: {'⚫ Black' if next_player == 'B' else '⚪ White'}**\n"
    md += "🟩 **Current Board**\n\n"

    # Header kolom
    md += "|   | A | B | C | D | E | F | G | H |\n"
    md += "|---|---|---|---|---|---|---|---|---|\n"

    emoji_map = {
        ".": " ",
        "B": "⚫",
        "W": "⚪"
    }

    for row in range(8):
        md += f"| {8-row} "
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
    board, next_player = read_board()
    move_row, move_col = parse_move()
    board = apply_move(board, move_row, move_col, next_player)
    next_player = switch_player(next_player)
    write_board(board, next_player)
    render_readme(board, next_player)
