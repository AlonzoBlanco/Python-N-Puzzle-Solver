# N-Puzzle Solver

A desktop **N-Puzzle Solver** built with **Python** and **Pygame**. The project supports the classic **8-puzzle**, **15-puzzle**, and **24-puzzle**, allowing the user to generate random puzzles, enter custom configurations, solve them with informed search algorithms, visualize the solution step by step, and compare algorithm performance through statistics.

The solver uses **A\*** and **IDA\*** with the **Manhattan Distance + Linear Conflict** heuristic to find solutions efficiently while tracking execution time, generated nodes, expanded nodes, memory estimation, and solution length.

---

## Features

- Interactive Pygame interface.
- Support for three board sizes:
  - **8-Puzzle**: 3×3 board.
  - **15-Puzzle**: 4×4 board.
  - **24-Puzzle**: 5×5 board.
- Random puzzle generation by difficulty.
- Custom puzzle input with validation.
- Solvability checking before running the solver.
- Solver options:
  - **A\***
  - **IDA\***
  - **Compare Both**
- Step-by-step solution playback.
- Automatic playback mode.
- First/last state visualization.
- Statistics screen with algorithm performance metrics.
- Matplotlib-generated comparison charts when both algorithms are tested.

---

## How the Project Works

The program is divided into two main parts:

1. **Graphical user interface**
2. **Puzzle-solving logic**

The graphical interface is responsible for displaying menus, buttons, puzzle boards, solution playback, and statistics. The solving logic is handled separately by the `NPuzzle` class, which contains the board representation, puzzle generation, heuristic calculation, solvability test, and search algorithms.

---

## Application Flow

When the project starts, the user is taken to the main menu and can choose one of the supported puzzle sizes.

```text
8-Puzzle  -> 3×3 board
15-Puzzle -> 4×4 board
24-Puzzle -> 5×5 board
```

After selecting a puzzle size, the user can either:

- Generate a random puzzle.
- Enter a custom puzzle manually.

For random puzzles, the difficulty level controls how many legal shuffle moves are applied from the goal state. Since the board is shuffled using valid moves, generated puzzles are solvable by construction.

For custom puzzles, the user must enter all tile values exactly once, using `0` as the blank tile. The application validates the input before allowing the solver to run.

---

## Board Representation

Each puzzle state is represented as a flat Python tuple.

For example, a solved 3×3 board is stored as:

```python
(1, 2, 3,
 4, 5, 6,
 7, 8, 0)
```

Where `0` represents the empty space.

The goal state is automatically generated based on the selected board size:

```python
(1, 2, 3, ..., n - 1, 0)
```

For a 4×4 board, this means:

```python
(1, 2, 3, 4,
 5, 6, 7, 8,
 9, 10, 11, 12,
 13, 14, 15, 0)
```

---

## Solvability Check

Before solving a puzzle, the program checks whether the configuration is solvable.

The solver counts inversions in the tile sequence. For odd-sized boards, a puzzle is solvable when the number of inversions is even. For even-sized boards, the blank tile row from the bottom is also considered.

This prevents the program from wasting time on impossible configurations.

---

## Heuristic Function

Both algorithms use the same heuristic:

```text
Manhattan Distance + Linear Conflict
```

### Manhattan Distance

Manhattan Distance measures how far each tile is from its goal position using vertical and horizontal moves only.

### Linear Conflict

Linear Conflict improves the heuristic by detecting tiles that are already in their correct row or column but are blocking each other. Each conflict adds an extra cost of `2` moves.

This makes the heuristic more informed than Manhattan Distance alone and helps reduce the number of explored states.

---

## Algorithms

### A\*

A\* uses a priority queue to always expand the most promising state first.

Each state is evaluated with:

```text
f(n) = g(n) + h(n)
```

Where:

- `g(n)` is the number of moves from the initial state.
- `h(n)` is the estimated distance to the goal.
- `f(n)` is the total estimated cost.

A\* is usually fast for smaller puzzles, but it can consume a large amount of memory because it stores visited states, paths, and frontier nodes.

In this project, A\* is used for the 8-puzzle and 15-puzzle. It is disabled for the 24-puzzle in the interface because the memory requirements can become too large.

### IDA\*

IDA\* stands for **Iterative Deepening A\***.

It combines the heuristic idea of A\* with the lower memory usage of depth-first search. Instead of storing a large priority queue, IDA\* searches using a cost limit and gradually increases that limit until a solution is found.

IDA\* is more memory-efficient than A\*, making it a better option for larger puzzles like the 24-puzzle. However, it may take longer because it can revisit states across iterations.

---

## Statistics and Performance Metrics

After solving a puzzle, the application stores and displays solver statistics using the `SolverStats` data structure.

Tracked metrics include:

- Algorithm used.
- Puzzle size.
- Heuristic used.
- Solution length.
- Nodes expanded.
- Nodes generated.
- Execution time.
- Maximum frontier size or search depth.
- Estimated memory usage.
- Solver status.
- Solution path.

When using **Compare Both**, the program runs A\* and IDA\* and generates visual charts comparing:

- Execution time.
- Nodes expanded.
- Nodes generated.
- Estimated memory usage.

---

## Project Structure

The project is organized into GUI modules and solver modules.

```text
project/
│
├── main.py
├── requirements.txt
│
├── gui/
│   ├── app.py
│   ├── components.py
│   └── constants.py
│
└── models/
    └── puzzle.py
```

### `main.py`

Entry point of the application.

It creates an instance of the `App` class and starts the main loop.

```python
from gui.app import App

if __name__ == "__main__":
    App().run()
```

### `gui/app.py`

Contains the main Pygame application class.

Responsibilities:

- Controls the current screen.
- Handles user input.
- Manages buttons and navigation.
- Starts solving in a separate thread.
- Displays solution results.
- Handles playback modes.
- Builds the statistics screen.

Main screens include:

- Main menu.
- Puzzle selection menu.
- Difficulty selection.
- Custom input.
- Board preview.
- Solving screen.
- Result screen.
- Statistics screen.
- Step-by-step playback.
- First/last state view.

### `gui/components.py`

Contains reusable GUI helper functions and components.

Main elements:

- `Button` class.
- Rounded rectangle drawing helper.
- Text rendering helper.
- Puzzle board drawing function.

### `gui/constants.py`

Stores application constants such as:

- Window size.
- Colors.
- Fonts.
- Puzzle names and descriptions.
- Difficulty shuffle values.
- Screen identifiers.
- Time limit for hard searches.

### `models/puzzle.py`

Contains the core puzzle-solving logic.

Main elements:

- `SolverStats` dataclass.
- `NPuzzle` class.
- Puzzle generation.
- Solvability checking.
- Manhattan + Linear Conflict heuristic.
- A\* implementation.
- IDA\* implementation.

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repository-name.git
cd your-repository-name
```

### 2. Create a virtual environment

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Requirements

The project uses:

```text
pygame
matplotlib
numpy
```

These dependencies are listed in `requirements.txt`.

---

## How to Run

From the project root, run:

```bash
python main.py
```

Make sure the folder structure is correct before running the project. The imports expect `app.py`, `components.py`, and `constants.py` to be inside a `gui` folder, and `puzzle.py` to be inside a `models` folder.

---

## How to Use

1. Run the application.
2. Select the puzzle size:
   - 8-Puzzle
   - 15-Puzzle
   - 24-Puzzle
3. Choose whether to generate a random puzzle or enter a custom one.
4. If generating a puzzle, select a difficulty.
5. Preview the initial board.
6. Choose a solving mode:
   - A\*
   - IDA\*
   - Compare Both
7. Wait for the solver to finish.
8. Review the result.
9. View the solution using:
   - Play all steps.
   - First and last state only.
   - Automatic playback.
10. Open the statistics screen to inspect performance.

---

## Custom Puzzle Input Format

Custom puzzles should be entered as numbers separated by spaces or commas.

Example for a 3×3 puzzle:

```text
1 2 3 4 5 6 7 0 8
```

The blank tile must be represented with `0`.

The input must:

- Contain exactly `size × size` numbers.
- Include every number from `0` to `size² - 1` exactly once.
- Represent a solvable puzzle configuration.

---

## Notes About the 24-Puzzle

The 24-puzzle is significantly harder than the 8-puzzle and 15-puzzle because the search space is much larger.

For that reason:

- A\* is disabled for the 24-puzzle in the interface.
- IDA\* is the recommended algorithm for 5×5 boards.
- A time limit is used to avoid extremely long searches.
- Hard configurations may still take a long time or timeout.

---

## Possible Future Improvements

- Add exportable statistics reports.
- Save results from multiple runs for long-term analysis.
- Add more heuristics for comparison.
- Add pattern databases for better 15-puzzle and 24-puzzle performance.
- Add keyboard shortcuts for menu navigation.
- Add a pause/cancel button while solving.
- Add unit tests for the solver logic.
- Add screenshots or GIFs to the README.

---

## License

This project is intended for academic and educational use. Add a license file if you plan to publish it as an open-source repository.
