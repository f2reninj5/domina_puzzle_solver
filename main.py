from typing import TextIO, Any


class Position:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: Any) -> bool:
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))

    def __repr__(self) -> str:
        return f"({self.x}, {self.y})"


class Move:
    def __init__(self, prev: Position, to: Position) -> None:
        self.prev = prev
        self.to = to

    @property
    def opposite_to(self) -> Position:
        if self.to.y == self.prev.y:
            return Position((2 * self.prev.x) - self.to.x, self.to.y)
        else:
            return Position(self.to.x, (2 * self.prev.y) - self.to.y)


class Box(Position):
    pass


class Target(Position):
    pass


class PuzzleMap(list):
    def __init__(self, puzzle_map: list[list[int]]) -> None:
        super().__init__(puzzle_map)

    def __getitem__(self, key: Any):
        if isinstance(key, Position):
            return super().__getitem__(key.x)[key.y]

        return super().__getitem__(key)


class Puzzle:
    @staticmethod
    def parse_file(file: TextIO) -> tuple[PuzzleMap, frozenset[Box], frozenset[Target]]:
        puzzle_map: list[list[int]] = []
        boxes: set[Box] = set()
        targets: set[Target] = set()

        for i, line in enumerate(file):
            row = []
            line = line.strip()

            for j, character in enumerate(line):
                if character == "#":
                    row.append(0)
                else:
                    row.append(1)
                    if character == "O":
                        boxes.add(Box(i, j))
                    elif character == "X":
                        targets.add(Target(i, j))

            puzzle_map.append(row)

        return PuzzleMap(puzzle_map), frozenset(boxes), frozenset(targets)

    def __init__(self, path: str) -> None:
        file = open(path, "r")
        self.puzzle_map, self.boxes, self.targets = self.parse_file(file)
        self.width = len(self.puzzle_map[0])
        self.height = len(self.puzzle_map)

    def repr_state(self, boxes: frozenset[Box]) -> str:
        puzzle_map = [[" " if i else "#" for i in row] for row in self.puzzle_map]
        for box in boxes:
            puzzle_map[box.x][box.y] = "O"
        for target in self.targets:
            puzzle_map[target.x][target.y] = "X"
        return "\n".join("".join(row) for row in puzzle_map)

    def __repr__(self) -> str:
        return self.repr_state(self.boxes)

    def is_valid_move(self, move: Move) -> bool:
        return all(
            (
                0 <= move.to.x < self.width,  # within bounds x
                0 <= move.to.y < self.height,  # within bounds y
                move.to not in self.boxes,  # no box collision
                self.puzzle_map[move.to],  # no wall collision
                self.puzzle_map[move.opposite_to],  # has space to push from
            )
        )

    def get_possible_positions_for_box(self, box: Box) -> set[Box]:
        return set(
            position
            for position in (
                Box(box.x + 1, box.y),
                Box(box.x - 1, box.y),
                Box(box.x, box.y + 1),
                Box(box.x, box.y - 1),
            )
            if self.is_valid_move(Move(box, position))
        )

    def get_possible_states(self) -> set[frozenset[Box]]:
        moves = set()

        for box in self.boxes:
            for box_move in self.get_possible_positions_for_box(box):
                move = frozenset(self.boxes - {box})
                move |= {box_move}
                moves.add(move)

        return moves


puzzle = Puzzle("puzzle.txt")
for state in puzzle.get_possible_states():
    print(puzzle.repr_state(state))
