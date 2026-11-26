import os, random, sys, tempfile, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import puzzlegen as pg

def _read(p):
    with open(p, "rb") as f: return f.read()

class T(unittest.TestCase):
    def test_sudoku_unique_and_consistent(self):
        rng = random.Random(3)
        for d in ("easy", "medium", "hard"):
            puz, sol = pg.make_sudoku(rng, d)
            self.assertEqual(pg.count_solutions([r[:] for r in puz]), 1)
            for r in range(9):
                for c in range(9):
                    if puz[r][c]: self.assertEqual(puz[r][c], sol[r][c])
            for i in range(9):
                self.assertEqual(sorted(sol[i]), list(range(1, 10)))
                self.assertEqual(sorted(sol[r][i] for r in range(9)), list(range(1, 10)))
    def test_wordsearch_words_are_in_grid(self):
        rng = random.Random(5); words = ["CAT", "DOG", "BIRD", "FISH", "HORSE"]
        for d in ("easy", "medium", "hard"):
            grid, placed, mark = pg.make_wordsearch(rng, words, 12, d)
            self.assertEqual(placed, sorted(words))
            lines = ["".join(r) for r in grid] + ["".join(grid[r][c] for r in range(12)) for c in range(12)]
            if d == "easy": self.assertTrue(all(any(w in l for l in lines) for w in words))
    def test_maze_is_perfect(self):
        m, path = pg.make_maze(random.Random(1), 10)
        edges = sum(len(v) for v in m.values()) // 2
        self.assertEqual(edges, 99)  # spanning tree of 100 cells
        self.assertEqual((path[0], path[-1]), ((0, 0), (9, 9)))
    def test_pdf_even_pages_and_header(self):
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, "a.pdf"); pg.main(["--type", "sudoku", "--count", "3", "--seed", "2", "-o", out])
            data = _read(out); self.assertTrue(data.startswith(b"%PDF-1.4")); self.assertTrue(data.rstrip().endswith(b"%%EOF"))
            self.assertEqual(data.count(b"/Type /Page ") % 2, 0)
    def test_same_seed_same_book(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = os.path.join(d, "a.pdf"), os.path.join(d, "b.pdf")
            pg.main(["--type", "maze", "--count", "2", "--size", "8", "--seed", "9", "-o", a]); pg.main(["--type", "maze", "--count", "2", "--size", "8", "--seed", "9", "-o", b])
            self.assertEqual(_read(a), _read(b))
if __name__ == "__main__": unittest.main()
