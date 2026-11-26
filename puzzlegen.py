#!/usr/bin/env python3
"""puzzlegen: make Sudoku, word search and maze puzzle books as a print-ready PDF. Pure Python 3.8+, no dependencies.

Example:
    python puzzlegen.py --type sudoku --count 20 --difficulty medium --trim 6x9 --seed 7 -o sudoku.pdf
    python puzzlegen.py --type wordsearch --words animals.txt --count 10 --trim 8.5x11 -o words.pdf
    python puzzlegen.py --type maze --count 12 --size 20 -o mazes.pdf

Every Sudoku is solver-checked for exactly one solution. Word search and maze use a seed, so a new seed gives a new volume.
"""
import argparse, random, sys, string
from collections import deque

TRIMS = {"5.5x8.5": (5.5, 8.5), "6x9": (6, 9), "7x10": (7, 10), "8x10": (8, 10), "8.5x11": (8.5, 11)}
CLUES = {"easy": 40, "medium": 32, "hard": 26}
DIRS_EASY = [(0, 1), (1, 0)]
DIRS_MED = DIRS_EASY + [(1, 1), (-1, 1)]
DIRS_HARD = DIRS_MED + [(0, -1), (-1, 0), (-1, -1), (1, -1)]

# ---------------------------------------------------------------- Sudoku
def _candidates(g, r, c):
    used = set(g[r]) | {g[i][c] for i in range(9)}
    br, bc = r // 3 * 3, c // 3 * 3
    used |= {g[i][j] for i in range(br, br + 3) for j in range(bc, bc + 3)}
    return [v for v in range(1, 10) if v not in used]

def count_solutions(g, limit=2):
    """Number of solutions of grid g (0 = empty), stopping at `limit`."""
    best = None
    for r in range(9):
        for c in range(9):
            if g[r][c] == 0:
                cand = _candidates(g, r, c)
                if best is None or len(cand) < len(best[2]):
                    best = (r, c, cand)
                    if not cand: return 0
    if best is None: return 1
    r, c, cand = best; n = 0
    for v in cand:
        g[r][c] = v; n += count_solutions(g, limit - n); g[r][c] = 0
        if n >= limit: break
    return n

def full_grid(rng):
    g = [[0] * 9 for _ in range(9)]
    def fill(pos):
        if pos == 81: return True
        r, c = divmod(pos, 9); cand = _candidates(g, r, c); rng.shuffle(cand)
        for v in cand:
            g[r][c] = v
            if fill(pos + 1): return True
        g[r][c] = 0; return False
    fill(0); return g

def make_sudoku(rng, difficulty="medium"):
    sol = full_grid(rng); puz = [row[:] for row in sol]; target = CLUES[difficulty]
    cells = [(r, c) for r in range(9) for c in range(9)]; rng.shuffle(cells); left = 81
    for r, c in cells:
        if left <= target: break
        keep = puz[r][c]; puz[r][c] = 0
        if count_solutions([row[:] for row in puz]) != 1: puz[r][c] = keep
        else: left -= 1
    return puz, sol

# ---------------------------------------------------------------- Word search
def make_wordsearch(rng, words, size, difficulty="easy"):
    dirs = {"easy": DIRS_EASY, "medium": DIRS_MED, "hard": DIRS_HARD}[difficulty]
    words = sorted({w.upper() for w in words if w.isalpha() and 2 <= len(w) <= size}, key=len, reverse=True)
    grid = [[""] * size for _ in range(size)]; placed = {}
    for w in words:
        for _ in range(400):
            dr, dc = rng.choice(dirs); r, c = rng.randrange(size), rng.randrange(size)
            er, ec = r + dr * (len(w) - 1), c + dc * (len(w) - 1)
            if not (0 <= er < size and 0 <= ec < size): continue
            cells = [(r + dr * i, c + dc * i) for i in range(len(w))]
            if all(grid[a][b] in ("", w[i]) for i, (a, b) in enumerate(cells)):
                for i, (a, b) in enumerate(cells): grid[a][b] = w[i]
                placed[w] = cells; break
    mark = {cell for cells in placed.values() for cell in cells}
    for r in range(size):
        for c in range(size):
            if not grid[r][c]: grid[r][c] = rng.choice(string.ascii_uppercase)
    return grid, sorted(placed), mark

# ---------------------------------------------------------------- Maze (perfect maze, recursive backtracker)
def make_maze(rng, n):
    open_ = {(r, c): set() for r in range(n) for c in range(n)}; seen = {(0, 0)}; stack = [(0, 0)]
    while stack:
        r, c = stack[-1]
        nb = [(r + a, c + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (r + a, c + b) in open_ and (r + a, c + b) not in seen]
        if not nb: stack.pop(); continue
        nxt = rng.choice(nb); open_[(r, c)].add(nxt); open_[nxt].add((r, c)); seen.add(nxt); stack.append(nxt)
    prev = {(0, 0): None}; q = deque([(0, 0)])
    while q:
        cur = q.popleft()
        for nx in open_[cur]:
            if nx not in prev: prev[nx] = cur; q.append(nx)
    path = []; cur = (n - 1, n - 1)
    while cur: path.append(cur); cur = prev[cur]
    return open_, path[::-1]

# ---------------------------------------------------------------- Tiny PDF writer
class PDF:
    def __init__(self, w, h): self.w, self.h, self.pages, self.cur = w, h, [], None
    def new_page(self): self.cur = []; self.pages.append(self.cur)
    def _o(self, s): self.cur.append(s)
    def line(self, x1, y1, x2, y2, lw=1, gray=0): self._o(f"{gray:.2f} G {lw:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S")
    def rgb_line(self, pts, lw, rgb):
        self._o(f"{rgb[0]} {rgb[1]} {rgb[2]} RG {lw:.2f} w {pts[0][0]:.2f} {pts[0][1]:.2f} m " + " ".join(f"{x:.2f} {y:.2f} l" for x, y in pts[1:]) + " S 0 G")
    def text(self, x, y, s, size=12, bold=False, gray=0, center=False):
        s = "".join(ch if ord(ch) < 128 else "?" for ch in s)
        if center: x -= 0.28 * size * len(s)  # Helvetica average glyph ~0.56em
        s = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self._o(f"BT {gray:.2f} g /{'F2' if bold else 'F1'} {size} Tf {x:.2f} {y:.2f} Td ({s}) Tj ET 0 g")
    def save(self, path):
        if len(self.pages) % 2: self.new_page()  # KDP needs an even page count
        objs = [b"<< /Type /Catalog /Pages 2 0 R >>", None,
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"]
        kids = []
        for pg in self.pages:
            stream = "\n".join(pg).encode("latin-1"); n = len(objs)
            objs.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.w:.2f} {self.h:.2f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {n + 2} 0 R >>".encode())
            objs.append(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream"); kids.append(f"{n + 1} 0 R")
        objs[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(kids)} >>".encode()
        out = bytearray(b"%PDF-1.4\n"); offs = []
        for i, o in enumerate(objs, 1): offs.append(len(out)); out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
        x = len(out); out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
        for o in offs: out += f"{o:010d} 00000 n \n".encode()
        out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF\n".encode()
        with open(path, "wb") as fh: fh.write(out)

# ---------------------------------------------------------------- Page drawing
class Layout:
    def __init__(self, pdf, page_no):  # mirrored margins: wider inside (gutter), 0.5in outside/top/bottom
        inside, outside = 0.625 * 72, 0.5 * 72
        odd = page_no % 2 == 1
        self.left = inside if odd else outside; self.right = pdf.w - (outside if odd else inside)
        self.top = pdf.h - 0.6 * 72; self.bottom = 0.6 * 72
        self.cx = (self.left + self.right) / 2

def sudoku_grid(pdf, grid, x0, y0, size, given=None):
    cell = size / 9
    for i in range(10):
        lw = 2.2 if i % 3 == 0 else 0.6
        pdf.line(x0 + i * cell, y0, x0 + i * cell, y0 + size, lw); pdf.line(x0, y0 + i * cell, x0 + size, y0 + i * cell, lw)
    for r in range(9):
        for c in range(9):
            v = grid[r][c]
            if v:
                g = 0.5 if (given is not None and given[r][c] == 0) else 0
                pdf.text(x0 + c * cell + cell / 2, y0 + size - r * cell - cell * 0.72, str(v), cell * 0.6, bold=g == 0, gray=g, center=True)

def build_sudoku_book(pdf, count, diff, rng, title):
    puzzles = [make_sudoku(rng, diff) for _ in range(count)]
    title_page(pdf, title, f"{count} {diff} Sudoku puzzles")
    for i, (p, _) in enumerate(puzzles, 1):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); size = min(L.right - L.left, L.top - L.bottom - 70)
        pdf.text(L.cx, L.top - 18, f"Puzzle {i}  ({diff.title()})", 18, True, center=True)
        sudoku_grid(pdf, p, L.cx - size / 2, L.top - 40 - size, size)
    answer_header(pdf); per = 4
    for k in range(0, count, per):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); w = (L.right - L.left - 30) / 2
        for j, idx in enumerate(range(k, min(k + per, count))):
            cx, cy = j % 2, j // 2; x0 = L.left + cx * (w + 30); y0 = L.top - 30 - (cy + 1) * (w + 40) + 20
            pdf.text(x0, y0 + w + 6, f"Puzzle {idx + 1}", 10, True); sudoku_grid(pdf, puzzles[idx][1], x0, y0, w, given=puzzles[idx][0])

def title_page(pdf, title, sub):
    pdf.new_page(); pdf.text(pdf.w / 2, pdf.h * 0.62, title, 28, True, center=True); pdf.text(pdf.w / 2, pdf.h * 0.62 - 30, sub, 14, center=True)
    pdf.text(pdf.w / 2, pdf.h * 0.62 - 60, "Made with puzzlegen (open source)", 10, gray=0.4, center=True)

def answer_header(pdf):
    pdf.new_page(); pdf.text(pdf.w / 2, pdf.h * 0.55, "Solutions", 28, True, center=True)

def letters_grid(pdf, grid, x0, y0, size, mark=None):
    n = len(grid); cell = size / n
    for r in range(n):
        for c in range(n):
            hit = mark is None or (r, c) in mark
            pdf.text(x0 + c * cell + cell / 2, y0 + size - r * cell - cell * 0.7, grid[r][c], cell * 0.62, bold=bool(mark is not None and hit), gray=0 if hit else 0.75, center=True)

def build_wordsearch_book(pdf, count, diff, rng, title, words, grid_size):
    data = []
    for i in range(count):
        w = rng.sample(words, min(len(words), 12)) if len(words) > 12 else words
        data.append(make_wordsearch(rng, w, grid_size, diff))
    title_page(pdf, title, f"{count} word search puzzles ({diff})")
    for i, (g, wl, _) in enumerate(data, 1):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); size = min(L.right - L.left, (L.top - L.bottom) * 0.62)
        pdf.text(L.cx, L.top - 18, f"Puzzle {i}", 18, True, center=True)
        letters_grid(pdf, g, L.cx - size / 2, L.top - 40 - size, size)
        y = L.top - 60 - size; cols = 3; cw = (L.right - L.left) / cols
        for k, w in enumerate(wl): pdf.text(L.left + (k % cols) * cw, y - (k // cols) * 14, w, 11)
    answer_header(pdf)
    for k in range(0, count, 2):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); size = min(L.right - L.left, (L.top - L.bottom) / 2 - 40)
        for j, idx in enumerate(range(k, min(k + 2, count))):
            y0 = L.top - 30 - (j + 1) * (size + 30) + 15
            pdf.text(L.left, y0 + size + 6, f"Puzzle {idx + 1}", 10, True); letters_grid(pdf, data[idx][0], L.cx - size / 2, y0, size, data[idx][2])

def maze_draw(pdf, maze, n, x0, y0, size, path=None):
    cell = size / n
    def seg(a, b): pdf.line(*a, *b, 1.4)
    for r in range(n):
        for c in range(n):
            X, Y = x0 + c * cell, y0 + size - r * cell
            if r == 0 and c != 0: seg((X, Y), (X + cell, Y))            # top wall (entrance at top-left)
            if (r, c + 1) not in maze[(r, c)] and not (c == n - 1 and r == n - 1): seg((X + cell, Y), (X + cell, Y - cell))
            if (r + 1, c) not in maze[(r, c)] and not (r == n - 1 and c == n - 1): seg((X, Y - cell), (X + cell, Y - cell))
            if c == 0 and r != 0: seg((X, Y), (X, Y - cell))
    if path: pdf.rgb_line([(x0 + c * cell + cell / 2, y0 + size - r * cell - cell / 2) for r, c in path], 2, (0.85, 0.1, 0.1))

def build_maze_book(pdf, count, rng, title, n):
    data = [make_maze(rng, n) for _ in range(count)]
    title_page(pdf, title, f"{count} mazes ({n} x {n})")
    for i, (m, _) in enumerate(data, 1):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); size = min(L.right - L.left, L.top - L.bottom - 70)
        pdf.text(L.cx, L.top - 18, f"Maze {i}   Start: top left   Finish: bottom right", 13, True, center=True)
        maze_draw(pdf, m, n, L.cx - size / 2, L.top - 40 - size, size)
    answer_header(pdf)
    for k in range(0, count, 2):
        pdf.new_page(); L = Layout(pdf, len(pdf.pages)); size = min(L.right - L.left, (L.top - L.bottom) / 2 - 40)
        for j, idx in enumerate(range(k, min(k + 2, count))):
            y0 = L.top - 30 - (j + 1) * (size + 30) + 15
            pdf.text(L.left, y0 + size + 6, f"Maze {idx + 1}", 10, True); maze_draw(pdf, data[idx][0], n, L.cx - size / 2, y0, size, data[idx][1])

def main(argv=None):
    ap = argparse.ArgumentParser(description="Make Sudoku, word search or maze puzzle books as a PDF.")
    ap.add_argument("--type", choices=["sudoku", "wordsearch", "maze"], required=True)
    ap.add_argument("--count", type=int, default=10, help="puzzles in the book (default 10)")
    ap.add_argument("--difficulty", choices=["easy", "medium", "hard"], default="medium")
    ap.add_argument("--trim", choices=sorted(TRIMS), default="6x9", help="page size in inches")
    ap.add_argument("--words", help="text file, one word per line (word search)")
    ap.add_argument("--size", type=int, default=15, help="grid size for word search / maze (default 15)")
    ap.add_argument("--seed", type=int, default=1, help="same seed = same book; change it for the next volume")
    ap.add_argument("--title", default=None); ap.add_argument("-o", "--output", default="puzzles.pdf")
    a = ap.parse_args(argv); rng = random.Random(a.seed); w, h = (v * 72 for v in TRIMS[a.trim]); pdf = PDF(w, h)
    if a.type == "sudoku": build_sudoku_book(pdf, a.count, a.difficulty, rng, a.title or "Sudoku Puzzle Book")
    elif a.type == "wordsearch":
        if not a.words: ap.error("--words FILE is required for word search")
        with open(a.words) as fh: words = [x.strip() for x in fh if x.strip()]
        build_wordsearch_book(pdf, a.count, a.difficulty, rng, a.title or "Word Search Puzzle Book", words, a.size)
    else: build_maze_book(pdf, a.count, rng, a.title or "Maze Puzzle Book", a.size)
    pdf.save(a.output); print(f"wrote {a.output}: {len(pdf.pages)} pages, {a.trim} in")

if __name__ == "__main__": main()
