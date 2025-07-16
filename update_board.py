import os
import re
import json

BOARD_FILE = "board.txt"
README_FILE = "README.md"

def init_board():
    return [
        list("........"),
        list("........"),
        list("........"),
        list("...WB..."),
        list("...BW..."),
        list("........"),
        list("........"),
        list("........")
    ]

def read_board():
    with open(BOARD_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines()]
    board = [list(line) for line in lines[:8]]
    next_player = lines[-1].split(":")[1].strip()
    return board, next_player

def write_board(board, next_player):
    with open(BOARD_FILE, "w", encoding="utf-8") as f:
        for row in board:
            f.write("".join(row) + "\n")
        f.write(f"\nNext: {next_player}\n")

def parse_event():
    with open(os.environ['GITHUB_EVENT_PATH'], 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_move(title):
    match = re.search(r"^[Mm]ove:\s*([A-Ha-h][1-8])", title.strip())
    if not match:
        raise ValueError("❌ Invalid move format. Use 'move: D3' at the beginning of the title.")

    move = match.group(1).upper()
    col = ord(move[0]) - ord('A')
    row = 8 - int(move[1])
    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise ValueError("❌ Move out of bounds. Use A1 to H8.")
    return row, col

def apply_move(board, row, col, player):
    if board[row][col] != ".":
        raise ValueError(f"❌ Cell {chr(col + ord('A'))}{8 - row} is already occupied.")

    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    to_flip = []
    opponent = "W" if player == "B" else "B"

    for dr, dc in directions:
        r, c = row + dr, col + dc
        temp = []
        while 0 <= r < 8 and 0 <= c < 8 and board[r][c] == opponent:
            temp.append((r, c))
            r += dr
            c += dc
        if 0 <= r < 8 and 0 <= c < 8 and board[r][c] == player and temp:
            to_flip.extend(temp)

    if not to_flip:
        raise ValueError("❌ Invalid move. No opponent pieces to flip.")

    board[row][col] = player
    for r, c in to_flip:
        board[r][c] = player

    return board

def switch_player(player):
    return "W" if player == "B" else "B"

def is_board_full(board):
    return all(cell != "." for row in board for cell in row)

def count_score(board):
    black = sum(row.count("B") for row in board)
    white = sum(row.count("W") for row in board)
    return black, white

def generate_game_md(board, next_player):
    md = "🟩 **Current Board**\n\n"
    md += "|   | A | B | C | D | E | F | G | H |\n"
    md += "|---|---|---|---|---|---|---|---|---|\n"

    emoji = { ".": " ", "B": "⚫", "W": "⚪" }
    for row in range(8):
        md += f"| {8 - row} "
        for col in range(8):
            md += f"| {emoji.get(board[row][col], ' ')} "
        md += "|\n"

    if is_board_full(board):
        black_score, white_score = count_score(board)
        md += "\n🏁 **Game Over!**\n"
        md += f"🔢 Final Score: ⚫ Black = {black_score}, ⚪ White = {white_score}\n"
        if black_score > white_score:
            md += "🎉 **Black Wins!**"
        elif white_score > black_score:
            md += "🎉 **White Wins!**"
        else:
            md += "🤝 **It's a Draw!**"
    else:
        md += f"\n✅ **Next turn: {'⚫ Black' if next_player == 'B' else '⚪ White'}**"

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
        event = parse_event()
        title = event["issue"]["title"]

        if title.lower().startswith("reset:"):
            board = init_board()
            next_player = "B"
            write_board(board, next_player)
            render_readme(board, next_player)
            print("✅ Game reset.")
            exit(0)

        board, next_player = read_board()
        move_row, move_col = parse_move(title)
        board = apply_move(board, move_row, move_col, next_player)
        next_player = switch_player(next_player)
        write_board(board, next_player)
        render_readme(board, next_player)

    except Exception as e:
        print(f"::error::{e}")
        exit(1)
