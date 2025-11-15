#!/usr/bin/env python3
"""
2048 Game with Bitboard AI
Clean, optimized implementation
"""

import tkinter as tk
from tkinter import messagebox
import random
import time
import rust_ai_2048

class Game2048:
    def __init__(self):
        try:
            self.root = tk.Tk()
            self.root.title("2048 Game with AI")
            self.root.configure(bg='#faf8ef')
            self.root.resizable(False, False)

            # Add protocol handler to prevent accidental closing
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # Game state
            self.board = [[0] * 4 for _ in range(4)]
            self.score = 0
            self.best_score = 0
            print("Creating AI instance...")
            self.ai = rust_ai_2048.ChampionAI()  # Original AI for GUI demo
            print("AI instance created successfully")
            self.ai_running = False
            print("AI running flag set")
        except Exception as e:
            print(f"Error during initialization: {e}")
            import traceback
            traceback.print_exc()
            raise

        # Tile colors
        self.colors = {
            0: "#cdc1b4", 2: "#eee4da", 4: "#ede0c8", 8: "#f2b179",
            16: "#f59563", 32: "#f67c5f", 64: "#f65e3b", 128: "#edcf72",
            256: "#edcc61", 512: "#edc850", 1024: "#edc53f", 2048: "#edc22e",
            4096: "#edc22e", 8192: "#edc22e"
        }
        print("Colors dictionary created")

        print("Calling setup_gui...")
        self.setup_gui()
        print("setup_gui completed")

        print("Calling new_game...")
        self.new_game()
        print("new_game completed")

        # Set window size and center it
        self.root.geometry("500x600")
        self.root.update_idletasks()

        # Center window on screen
        x = (self.root.winfo_screenwidth() // 2) - 250
        y = (self.root.winfo_screenheight() // 2) - 300
        self.root.geometry(f"500x600+{x}+{y}")
        print(f"Window positioned at {x},{y}")

    def setup_gui(self):
        main_container = tk.Frame(self.root, bg='#faf8ef')
        main_container.pack(padx=20, pady=20)

        # Title
        title = tk.Label(main_container, text="2048", font=("Arial", 48, "bold"),
                        bg='#faf8ef', fg='#776e65')
        title.pack(pady=(0, 10))

        # Score display
        score_frame = tk.Frame(main_container, bg='#faf8ef')
        score_frame.pack(pady=(0, 20))

        score_bg = tk.Frame(score_frame, bg='#bbada0', padx=10, pady=5)
        score_bg.pack(side="left", padx=5)
        tk.Label(score_bg, text="Score", font=("Arial", 10),
                bg='#bbada0', fg='#eee4da').pack()
        self.score_label = tk.Label(score_bg, text="0", font=("Arial", 20, "bold"),
                                    bg='#bbada0', fg='white')
        self.score_label.pack()

        best_bg = tk.Frame(score_frame, bg='#bbada0', padx=10, pady=5)
        best_bg.pack(side="left", padx=5)
        tk.Label(best_bg, text="Best", font=("Arial", 10),
                bg='#bbada0', fg='#eee4da').pack()
        self.best_label = tk.Label(best_bg, text="0", font=("Arial", 20, "bold"),
                                   bg='#bbada0', fg='white')
        self.best_label.pack()

        # Game board
        board_container = tk.Frame(main_container, bg='#bbada0', padx=5, pady=5)
        board_container.pack()

        self.tiles = []
        for i in range(4):
            row = []
            for j in range(4):
                cell_frame = tk.Frame(board_container, bg="#cdc1b4", width=70, height=70)
                cell_frame.grid(row=i, column=j, padx=5, pady=5)
                cell_frame.pack_propagate(False)

                label = tk.Label(cell_frame, text="", bg="#cdc1b4",
                               font=("Arial", 32, "bold"), fg='#776e65')
                label.pack(expand=True)
                row.append(label)
            self.tiles.append(row)

        # AI Controls
        ai_frame = tk.Frame(main_container, bg='#faf8ef')
        ai_frame.pack(pady=(20, 0))

        self.ai_button_frame = tk.Frame(ai_frame, bg='#8f7a66', padx=15, pady=10)
        self.ai_button_frame.pack(side="left", padx=5)
        self.ai_button_frame.bind("<Button-1>", self.toggle_ai)

        self.ai_button_label = tk.Label(self.ai_button_frame, text="▶ Start AI",
                                       font=("Arial", 14, "bold"), bg='#8f7a66', fg='#f9f6f2')
        self.ai_button_label.pack()
        self.ai_button_label.bind("<Button-1>", self.toggle_ai)

        # Instructions
        inst = tk.Label(main_container, text="Use arrow keys or click Start AI!",
                       font=("Arial", 12), bg='#faf8ef', fg='#776e65')
        inst.pack(pady=(10, 0))

        # Key bindings
        self.root.bind('<Up>', lambda e: self.move('up'))
        self.root.bind('<Down>', lambda e: self.move('down'))
        self.root.bind('<Left>', lambda e: self.move('left'))
        self.root.bind('<Right>', lambda e: self.move('right'))
        self.root.bind('w', lambda e: self.move('up'))
        self.root.bind('s', lambda e: self.move('down'))
        self.root.bind('a', lambda e: self.move('left'))
        self.root.bind('d', lambda e: self.move('right'))

        # Make window focusable for key events
        self.root.focus_set()

    def new_game(self):
        self.board = [[0] * 4 for _ in range(4)]
        self.score = 0
        self.ai_running = False
        self.ai_button_label.config(text="▶ Start AI", bg='#8f7a66')
        self.ai_button_frame.config(bg='#8f7a66')
        self.add_tile()
        self.add_tile()
        self.update_display()

    def add_tile(self):
        empty = [(i, j) for i in range(4) for j in range(4) if self.board[i][j] == 0]
        if empty:
            i, j = random.choice(empty)
            self.board[i][j] = 2 if random.random() < 0.9 else 4

    def update_display(self):
        for i in range(4):
            for j in range(4):
                value = self.board[i][j]
                label = self.tiles[i][j]
                if value == 0:
                    label.config(text="", bg="#cdc1b4")
                    label.master.config(bg="#cdc1b4")
                else:
                    bg_color = self.colors.get(value, "#3c3a32")
                    fg_color = '#f9f6f2' if value >= 8 else '#776e65'
                    font_size = 32 if value < 100 else 28 if value < 1000 else 24
                    label.config(text=str(value), bg=bg_color, fg=fg_color,
                               font=("Arial", font_size, "bold"))
                    label.master.config(bg=bg_color)

        self.score_label.config(text=str(self.score))
        if self.score > self.best_score:
            self.best_score = self.score
            self.best_label.config(text=str(self.best_score))

        # Update display
        try:
            self.root.update_idletasks()
        except Exception:
            pass  # Ignore if window is closing

    def move(self, direction, force=False):
        # Only block manual moves, not AI moves
        if self.ai_running and not force:
            return

        old_board = [row[:] for row in self.board]

        if direction == 'left':
            self.move_left()
        elif direction == 'right':
            self.move_right()
        elif direction == 'up':
            self.move_up()
        elif direction == 'down':
            self.move_down()

        if old_board != self.board:
            self.add_tile()
            self.update_display()
            # Only check game state for manual moves, AI handles its own game over detection
            if not force:
                self.check_game_state()
            return True  # Move was successful
        return False  # No change occurred

    def move_left(self):
        for i in range(4):
            row = [v for v in self.board[i] if v != 0]
            merged = []
            j = 0
            while j < len(row):
                if j + 1 < len(row) and row[j] == row[j + 1]:
                    merged.append(row[j] * 2)
                    self.score += row[j] * 2
                    j += 2
                else:
                    merged.append(row[j])
                    j += 1
            merged += [0] * (4 - len(merged))
            self.board[i] = merged

    def move_right(self):
        for i in range(4):
            row = [v for v in self.board[i] if v != 0]
            merged = []
            j = len(row) - 1
            while j >= 0:
                if j - 1 >= 0 and row[j] == row[j - 1]:
                    merged.insert(0, row[j] * 2)
                    self.score += row[j] * 2
                    j -= 2
                else:
                    merged.insert(0, row[j])
                    j -= 1
            merged = [0] * (4 - len(merged)) + merged
            self.board[i] = merged

    def move_up(self):
        self.board = [list(row) for row in zip(*self.board)]
        self.move_left()
        self.board = [list(row) for row in zip(*self.board)]

    def move_down(self):
        self.board = [list(row) for row in zip(*self.board)]
        self.move_right()
        self.board = [list(row) for row in zip(*self.board)]

    def is_game_over(self):
        # Check for empty cells
        for row in self.board:
            if 0 in row:
                return False

        # Check for possible merges
        for i in range(4):
            for j in range(4):
                current = self.board[i][j]
                if j < 3 and current == self.board[i][j + 1]:
                    return False
                if i < 3 and current == self.board[i + 1][j]:
                    return False
        return True

    def check_game_state(self):
        # Check for 2048
        for row in self.board:
            if 2048 in row:
                result = messagebox.askyesno("Congratulations!",
                                           "You reached 2048! Continue playing?")
                if not result:
                    self.new_game()
                return

        # Check game over
        if self.is_game_over():
            messagebox.showinfo("Game Over", f"Final Score: {self.score}")
            self.new_game()

    def toggle_ai(self, event=None):
        if self.ai_running:
            self.stop_ai()
        else:
            self.start_ai()

    def start_ai(self):
        self.ai_running = True
        self.ai_button_label.config(text="⏹ Stop AI", bg='#d32f2f')
        self.ai_button_frame.config(bg='#d32f2f')
        self.run_ai_step()

    def stop_ai(self):
        self.ai_running = False
        self.ai_button_label.config(text="▶ Start AI", bg='#8f7a66')
        self.ai_button_frame.config(bg='#8f7a66')

    def run_ai_step(self):
        if not self.ai_running:
            return

        if self.is_game_over():
            self.stop_ai()
            messagebox.showinfo("AI Game Over", f"AI Final Score: {self.score}")
            self.new_game()
            return

        try:
            start_time = time.time()
            move = self.ai.get_best_move(self.board)
            ai_time = time.time() - start_time
            print(f"AI suggests: {move} (took {ai_time:.3f}s)")

            if move:
                success = self.move(move, force=True)  # Force AI moves
                if success:
                    # Schedule next move with small delay for visualization
                    self.root.after(100, self.run_ai_step)
                else:
                    print("Move failed - no change occurred")
                    self.root.after(100, self.run_ai_step)
            else:
                self.stop_ai()
                messagebox.showinfo("AI Stuck", f"AI cannot find valid moves. Score: {self.score}")
        except Exception as e:
            print(f"AI Error: {e}")
            import traceback
            traceback.print_exc()
            self.stop_ai()
            messagebox.showerror("AI Error", f"AI encountered an error: {e}")

    def on_closing(self):
        """Handle window close event"""
        if self.ai_running:
            self.stop_ai()
        self.root.destroy()

    def run(self):
        print("🎮 2048 Game with Bitboard AI")
        print("Controls:")
        print("  • Arrow Keys or WASD: Manual play")
        print("  • Click 'Start AI': Watch AI play")
        print("  • Combine tiles to reach 2048!")
        print("Starting main loop...")
        try:
            self.root.mainloop()
        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    try:
        print("Initializing game...")
        game = Game2048()
        print("Game initialized, starting...")
        game.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()