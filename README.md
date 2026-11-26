# puzzlegen: a tiny open-source puzzle book generator

Make **Sudoku**, **word search** and **maze** puzzle books as a print-ready PDF from the command line. One Python file, **no dependencies**, MIT licensed.

```bash
python puzzlegen.py --type sudoku --count 20 --difficulty medium --trim 6x9 --seed 7 -o sudoku.pdf
python puzzlegen.py --type wordsearch --words examples/animals.txt --count 10 --trim 8.5x11 -o words.pdf
python puzzlegen.py --type maze --count 12 --size 20 --trim 6x9 -o mazes.pdf
```

Every book has a title page, one puzzle per page, a **solutions section**, and an **even page count** (printers like KDP require it). Samples: [`examples/`](examples/).

## Features

| | |
|---|---|
| **Sudoku** | Backtracking generator. Each puzzle is solver-checked and kept only if it has **exactly one solution**. Easy / medium / hard by clue count (40 / 32 / 26). |
| **Word search** | Your own word list (one word per line). Easy = across and down, medium adds diagonals, hard uses all 8 directions. Answer pages highlight every word. |
| **Maze** | Perfect mazes (one route, no loops) from a recursive backtracker. Solutions show the path. |
| **Trim sizes** | `5.5x8.5`, `6x9`, `7x10`, `8x10`, `8.5x11` inches. |
| **Seeds** | `--seed N` gives the same book every time. Change it for Vol. 2 so puzzles don't repeat. |
| **Zero dependencies** | Pure Python 3.8+. Writes the PDF itself. |

## Options

```
--type {sudoku,wordsearch,maze}   required
--count N                         puzzles in the book (default 10)
--difficulty {easy,medium,hard}   default medium
--trim {5.5x8.5,6x9,7x10,8x10,8.5x11}
--words FILE                      word list for word search
--size N                          grid size for word search / maze (default 15)
--seed N                          default 1
--title TEXT   -o FILE
```

## Using the PDF for Amazon KDP

Pages use mirrored margins (0.625 in inside, 0.5 in outside, top and bottom), which sit above the minimums KDP lists for most page counts. This is a simple layout, not a guarantee: **check KDP's current margin and bleed rules, view the PDF in KDP's previewer, and order a printed proof copy before you publish.** Fonts are the standard PDF Helvetica, so nothing needs embedding.

## Limits (by design)

- Plain layout: Helvetica, black and white, one puzzle per page. No covers, no page numbers, no artwork.
- Word search uses letters A to Z only. Sudoku is 9 x 9.
- Command line only. No preview.

## Want a point-and-click version?

[**PuzzleBind**](https://puzzlebind.com/?utm_source=github&utm_medium=repo&utm_campaign=puzzlegen_readme) is a Chrome extension that does this with a live preview, built for people publishing puzzle books on Amazon KDP: Sudoku, word search and mazes at KDP trim sizes, with Series Mode (Vol. 1, Vol. 2, ...), custom word lists from paste or CSV, saved presets and a large-print preset. It works offline and nothing is uploaded.

- Free plan: up to 20 puzzles per book, 1 export a day, small watermark. [Try the free web demo](https://puzzlebind.com/app/?utm_source=github&utm_medium=repo&utm_campaign=puzzlegen_readme)
- Pro: up to 200 pages per book, unlimited exports, no watermark. One payment, no subscription, 30-day refund. [See pricing](https://puzzlebind.com/pricing/?utm_source=github&utm_medium=repo&utm_campaign=puzzlegen_readme)
- Free guides for KDP puzzle publishers: [puzzlebind.com/guides](https://puzzlebind.com/guides/?utm_source=github&utm_medium=repo&utm_campaign=puzzlegen_readme)

You don't need PuzzleBind to use this repo. It is free and will stay free.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests cover: unique-solution Sudoku, word search placement, perfect mazes, PDF structure, and seed reproducibility. Pull requests are welcome: more grid types, page numbers, larger fonts, A4 trim.

## License

MIT, see [LICENSE](LICENSE).
