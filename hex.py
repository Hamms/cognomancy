import math
import constants


def linear_interpolation(a, b, t):
    return a + (b - a) * t


class Cube:
    """http://www.redblobgames.com/grids/hexagons/"""

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def __add__(self, other):
        return Cube(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z
        )

    def __eq__(self, other):
        return (self.x == other.x and
                self.y == other.y and
                self.z == other.z)

    def to_hex(self):
        q = self.x
        r = self.z
        return Hex(q, r)

    def distance(self, other):
        return (abs(self.x - other.x) +
                abs(self.y - other.y) +
                abs(self.z - other.z)) / 2

    def linedraw(self, other):
        if self == other:
            return [self]

        n = self.distance(other)
        results = []
        for i in range(int(n+1)):
            results.append(self.linear_interpolation(other, (1.0/n) * i).round())
        return results

    def round(self):
        rx = round(self.x)
        ry = round(self.y)
        rz = round(self.z)

        x_diff = abs(rx - self.x)
        y_diff = abs(ry - self.y)
        z_diff = abs(rz - self.z)

        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry-rz
        elif y_diff > z_diff:
            ry = -rx-rz
        else:
            rz = -rx-ry

        return Cube(rx, ry, rz)

    def linear_interpolation(self, other, t):
        return Cube(linear_interpolation(self.x, other.x, t),
                    linear_interpolation(self.y, other.y, t),
                    linear_interpolation(self.z, other.z, t))

    def neighbor(self, direction):
        return self + Cube.DIRECTIONS(direction)

    def range(self, dist):
        results = []
        for dx in range(-dist, dist+1):
            for dy in range(max(-dist, -dx-dist), min(dist, -dx+dist)+1):
                dz = -dx-dy
                results.append(self + Cube(dx, dy, dz))

    def reachable(self, movement):
        visited = set()
        visited.add(self)
        fringes = []
        fringes.append([self])

        for k in range(1, movement):
            fringes.append([])
            for cube in fringes[k]:
                for direction in Cube.directions:
                    neighbor = self + direction
                    # if neighbor not in visited and not neghbor.blocked:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        fringes[k].append(neighbor)

        return visited

Cube.DIRECTIONS = [
    Cube(+1, -1,  0), Cube(+1,  0, -1), Cube(0, +1, -1),
    Cube(-1, +1,  0), Cube(-1,  0, +1), Cube(0, -1, +1)
]


class Hex:
    """http://www.redblobgames.com/grids/hexagons/"""

    @staticmethod
    def pixel_to_hex(x, y):
        q = x * 2/3 / constants.TILE_SIZE
        r = (-x / 3 + math.sqrt(3)/3 * y) / constants.TILE_SIZE
        return Hex(q, r).round()

    @staticmethod
    def pixel_width():
        return constants.TILE_SIZE * 2

    @staticmethod
    def pixel_height():
        return math.sqrt(3)/2 * Hex.pixel_width()

    def pixel_center(self):
        x, y = self.to_pixel()
        return (x - self.pixel_width()/2, y - self.pixel_height()/2)

    def is_edge(self):
        return (self.column == 0 or self.row == -1 * math.floor(self.column/2) or
                self.column == constants.MAP_WIDTH - 1 or (self.row*2 + self.column) >= constants.MAP_WIDTH - 2)

    def __init__(self, column, row):
        self.column = column
        self.row = row

    def __str__(self):
        return "Hex({}, {})".format(self.column, self.row)

    def __eq__(self, other):
        return self.column == other.column and self.row == other.row

    def __add__(self, other):
        return Hex(
            self.column + other.column,
            self.row + other.row
        )

    def to_cube(self):
        x = self.column
        z = self.row
        y = -x-z
        return Cube(x, y, z)

    def distance(self, other):
        return (abs(self.column - other.column)
                + abs(self.column + self.row - other.column - other.row)
                + abs(self.row - other.row)) / 2

    def linedraw(self, other):
        return [
            result.to_hex() for result
            in self.to_cube().linedraw(other.to_cube())
        ]

    def round(self):
        return self.to_cube().round().to_hex()

    def linear_interpolation(self, other, t):
        return self.to_cube().linear_interpolation(other.to_cube(), t).to_hex()

    def neighbor(self, direction):
        return self + Hex.DIRECTIONS[direction]

    def range(self, dist):
        return [
            result.to_hex() for result
            in self.to_cube().range(dist)
        ]

    def reachable(self, movement):
        return [
            result.to_hex() for result
            in self.to_cube().reachable(movement)
        ]

    def to_pixel(self):
        x = constants.TILE_SIZE * 3/2 * self.column
        y = constants.TILE_SIZE * math.sqrt(3) * (self.row + self.column/2)
        return (x, y)

    def corner(self, i):
        angle_deg = 60 * i
        angle_rad = math.pi / 180 * angle_deg
        x, y = self.to_pixel()
        return (x + constants.TILE_SIZE * math.cos(angle_rad),
                y + constants.TILE_SIZE * math.sin(angle_rad))

Hex.DIRECTIONS = [
    Hex(+1, 0), Hex(+1, -1), Hex(0, -1),
    Hex(-1, 0), Hex(-1, +1), Hex(0, +1)
]
