from copy import deepcopy
from typing import TextIO, Any
import networkx as nx
from matplotlib import pyplot as plt


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

    @property
    def neighbours(self) -> set[Position]:
        return {
            Position(self.x + 1, self.y),
            Position(self.x - 1, self.y),
            Position(self.x, self.y + 1),
            Position(self.x, self.y - 1),
        }


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


class State:
    def __init__(self, boxes: frozenset[Box], player: Position) -> None:
        self.boxes = boxes
        self.player = player

    def __eq__(self, other: Any) -> bool:
        return self.boxes == other.boxes and self.player == other.player

    def __hash__(self) -> int:
        return hash((self.boxes, self.player))


class PuzzleMap(list):
    def __init__(self, puzzle_map: list[list[int]]) -> None:
        super().__init__(puzzle_map)

    def __getitem__(self, key: Any):
        if isinstance(key, Position):
            return super().__getitem__(key.x)[key.y]

        return super().__getitem__(key)

    def __setitem__(self, key: Any, value: int) -> None:
        if isinstance(key, Position):
            super().__getitem__(key.x)[key.y] = value
            return

        super().__setitem__(key, value)


class Puzzle:
    @staticmethod
    def parse_file(
        file: TextIO,
    ) -> tuple[PuzzleMap, frozenset[Box], frozenset[Target], Position]:
        puzzle_map: list[list[int]] = []
        boxes: set[Box] = set()
        targets: set[Target] = set()
        player = None

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
                    elif character == "*":
                        player = Position(i, j)

            puzzle_map.append(row)

        return PuzzleMap(puzzle_map), frozenset(boxes), frozenset(targets), player

    def __init__(self, path: str) -> None:
        file = open(path, "r")
        self.puzzle_map, self.boxes, self.targets, self.player = self.parse_file(file)
        self.initial_boxes = self.boxes.copy()
        self.width = len(self.puzzle_map[0])
        self.height = len(self.puzzle_map)
        possible_states = self.get_possible_states()
        self.states = {State(self.boxes, self.player): possible_states}
        self.state_queue = list(self.get_possible_states())

    @property
    def collision_map(self) -> PuzzleMap:
        puzzle_map = deepcopy(self.puzzle_map)
        for box in self.boxes:
            puzzle_map[box] = 0
        return puzzle_map

    @property
    def state(self) -> State:
        return State(self.boxes, self.player)

    @state.setter
    def state(self, state: State) -> None:
        self.boxes = state.boxes
        self.player = state.player

    @property
    def box_states(self) -> dict[frozenset[Box], set[frozenset[Box]]]:
        box_states = {}

        for state in self.states:
            box_state = state.boxes
            box_state_neighbours = set(map(lambda s: s.boxes, self.states[state]))
            if box_state not in box_states:
                box_states[box_state] = box_state_neighbours
            else:
                box_states[box_state] |= box_state_neighbours

        return box_states

    def repr_state(self, boxes: frozenset[Box], player: Position) -> str:
        puzzle_map = [[" " if i else "#" for i in row] for row in self.puzzle_map]
        for target in self.targets:
            puzzle_map[target.x][target.y] = "X"
        for box in boxes:
            puzzle_map[box.x][box.y] = "O"
        puzzle_map[player.x][player.y] = "*"
        return "\n".join("".join(row) for row in puzzle_map)

    def __repr__(self) -> str:
        return self.repr_state(self.boxes, self.player)

    def is_valid_move(self, move: Move) -> bool:
        return all(
            (
                0 <= move.to.x < self.width,  # within bounds x
                0 <= move.to.y < self.height,  # within bounds y
                move.to not in self.boxes,  # no box collision
                self.puzzle_map[move.to],  # no wall collision
                self.puzzle_map[move.opposite_to],  # has space to push away from wall
                move.opposite_to not in self.boxes,  # has space to push away from box
                self.is_reachable(move.opposite_to),
            )
        )

    def is_reachable(self, target: Position) -> bool:
        queue = [self.player]
        checked = set()

        while queue:
            position = queue.pop()

            for neighbour in position.neighbours:
                if neighbour not in checked and neighbour not in queue:
                    if not self.collision_map[neighbour]:
                        continue

                    if neighbour == target:
                        return True

                    queue.append(neighbour)

            checked.add(position)

        return False

    def get_possible_positions_for_box(self, box: Box) -> set[Box]:
        return set(
            position
            for position in box.neighbours
            if self.is_valid_move(Move(box, position))
        )

    def get_possible_states(self) -> set[frozenset[Box]]:
        states = set()

        for box in self.boxes:
            for box_move in self.get_possible_positions_for_box(box):
                move = frozenset(self.boxes - {box})
                move |= {box_move}
                states.add(State(move, box))

        return states

    def traverse_states(self) -> None:
        while self.state_queue:
            self.state = self.state_queue.pop()
            possible_states = self.get_possible_states()

            self.states[self.state] = possible_states

            for state in possible_states:
                if state not in self.state_queue and state not in self.states:
                    self.state_queue.append(state)


puzzle = Puzzle("puzzle.txt")
puzzle.traverse_states()

print("possible" if puzzle.targets in puzzle.box_states else "IMPOSSIBLE!!!!")

g = nx.DiGraph(puzzle.box_states)

if puzzle.targets in puzzle.box_states:
    path = nx.shortest_path(g, source=puzzle.initial_boxes, target=puzzle.targets)

    for box_state in path:
        print(puzzle.repr_state(box_state))

# print(puzzle.repr_state(puzzle.targets))
# for state in puzzle.states:
#     print("")
#     print(puzzle.repr_state(state))
#     for next_state in puzzle.states[state]:
#         print(puzzle.repr_state(next_state))


pos = nx.spring_layout(g)

plt.figure(figsize=(12, 12), dpi=300)

nx.draw_networkx_nodes(g, pos, node_size=10)
nx.draw_networkx_edges(g, pos, node_size=10, width=0.3, arrowsize=5, alpha=0.7)

plt.axis("off")
plt.tight_layout()
plt.show()
