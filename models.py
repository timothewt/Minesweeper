import random
import time
from math import log10
import pygame as pg
import numpy as np


class Grid:
    def __init__(self, grid_height: int = 0, grid_width: int = 0, bombs_nb: int = 0) -> None:
        if not bombs_nb > grid_height * grid_width:
            self.grid_height = grid_height
            self.grid_width = grid_width
            self.bombs_nb = bombs_nb
            self.bombs = []
            self.place_bombs()
            self.grid = np.full([self.grid_height, self.grid_width], -1, dtype=int)
            self.game_status = 0  # -1: player lost, 0: still playing, 1: player won
        else:
            self.grid = []

    def __str__(self) -> str:
        """
        Gives the grid as a string, where undiscovered cells are "■", discovered bomb is 9 and other numbers indicate
        how many bombs are next to the cell. "□" is a flagged cell suspected as a bomb
        :return: the grid, as a string
        """
        result = ''
        for row in self.grid:
            for cell in row:
                if cell == -1:
                    result += "■  "
                elif cell == -2:
                    result += "□  "
                else:
                    result += str(cell) + "  "
            result = result + '\n'
        return result

    def place_bombs(self) -> None:
        """
        Picks random cells where there will be bombs
        """
        placed_bombs = 0
        while placed_bombs < self.bombs_nb:
            random_cell = (random.randrange(self.grid_height), random.randrange(self.grid_width))
            if random_cell not in self.bombs:
                self.bombs.append(random_cell)
                placed_bombs += 1

    def get_neighbours(self, cell_coordinates):
        """
        Gives the coordinates of all the neighbours cells
        :param cell_coordinates: coordinates of the cell from which we want the neighbours
        :return: the list of neighbours
        """
        row = cell_coordinates[0]
        col = cell_coordinates[1]
        neighbours = [
            (row - 1, col - 1),
            (row - 1, col),
            (row - 1, col + 1),
            (row, col + 1),
            (row + 1, col + 1),
            (row + 1, col),
            (row + 1, col - 1),
            (row, col - 1)
        ]
        in_grid_neighbours = [cell for cell in neighbours if
                              0 <= cell[0] < self.grid_height and 0 <= cell[1] < self.grid_width]
        return in_grid_neighbours

    def check_for_bombs(self, cell_coordinates: tuple[int]) -> int:
        """
        Checks for bombs in the neighbours cells
        :param cell_coordinates: coordinates of the cell we want to check as (row, col)
        :return: 9 if the cell is a bomb, the number of bombs in the neighbours otherwise
        """
        if cell_coordinates in self.bombs:
            return 9
        near_bombs = 0
        neighbours = self.get_neighbours(cell_coordinates)
        for cell in neighbours:
            if cell in self.bombs:
                near_bombs += 1
        return near_bombs

    def discover_cell(self, cell_coordinates: tuple[int]) -> None:
        """
        Discovers a cell and all its neighbours until a bomb is near$
        :param cell_coordinates: coordinates of the cell we want to check as (row, col)
        """
        if self.grid[cell_coordinates] == -2:  # cannot discover a flagged cell
            return
        current_cell_bombs = self.check_for_bombs(cell_coordinates)
        self.grid[cell_coordinates] = current_cell_bombs
        if current_cell_bombs == 9:
            self.discover_all_non_flagged_bombs()
            self.grid[cell_coordinates] = 10  # indicates the bomb that made the player loose
            self.game_status = -1
        if current_cell_bombs == 0:  # if there are no bombs near, discovers all its neighbours
            neighbours = self.get_neighbours(cell_coordinates)
            undiscovered_neighbours = [neighbour for neighbour in neighbours if self.grid[neighbour] == -1]
            for neighbour in undiscovered_neighbours:
                self.discover_cell(neighbour)
        self.update_game_status()

    def discover_all_non_flagged_bombs(self) -> None:
        """
        Discovers all bombs in the grid except the one that was already discovered, the one that made the player loose,
        which has to display in red
        """
        for i in range(0, self.grid_height):
            for j in range(0, self.grid_width):
                if (i, j) in self.bombs:
                    if self.grid[i, j] != -2:  # we don't display a bomb on a flagged cell
                        self.grid[i, j] = 9
                elif self.grid[i, j] == -2:  # if we flagged a bomb
                    self.grid[i, j] = -3  # -3 means no bomb but flagged

    def get_remaining_non_flagged_bombs_nb(self):
        flags = self.grid == -2
        return max(0, self.bombs_nb - np.count_nonzero(flags))

    def flag_non_flagged_bombs(self) -> None:
        """
        Flags all non-flagged bombs
        """
        for bomb in self.bombs:
            if self.grid[bomb] == -1:
                self.grid[bomb] = -2

    def flag_cell(self, cell_coordinates: tuple[int]) -> bool:
        """
        Flags a cell suspected as a bomb
        :param cell_coordinates: coordinates of the cell suspected
        :return: True if the cell has been successfully flagged, False otherwise
        """
        if self.grid[cell_coordinates] == -1:
            self.grid[cell_coordinates] = -2
            return True
        if self.grid[cell_coordinates] == -2:
            self.grid[cell_coordinates] = -1
            return True
        return False

    def update_game_status(self) -> bool:
        """
        Counts the remaining undiscovered cells and compares it to the number of bombs
        :return: True if the player discovered all the non-bombs cells, False otherwise
        """
        non_discovered_cells = self.grid < 0  # -1 for non-flagged bombs, -2 for flagged bombs
        if np.count_nonzero(non_discovered_cells) == self.bombs_nb:
            self.game_status = 1
            self.flag_non_flagged_bombs()


class Timer:
    def __init__(self) -> None:
        self.start = time.time()
        self.time = 0

    def __str__(self) -> str:
        return f"Elapsed time: {self.time}s"

    def update(self) -> None:
        """
        Updates the time elapsed since the instantiation of the timer
        """
        self.time = int(time.time() - self.start)


class Game:
    def __init__(self):
        pg.init()
        self.difficulty = 0
        self.grid_width = 0
        self.grid_height = 0
        self.bombs_nb = 0
        self.screen = None
        self.grid = None
        self.flag_img = pg.image.load("assets/flag.png")
        self.bomb_img = pg.image.load("assets/bomb.png")
        self.no_bomb_img = pg.image.load("assets/no_bomb.png")
        self.timer = None
        self.buttons = None

    def draw_text(self, text: str, font_size: int, color: tuple[int], y: int, x: int = None, font: str = 'gothambold') -> None:
        """
        Draws a string on the current pygame screen. If x is not specified, the text is horizontally centered.
        :param text: string to write
        :param font_size: font size of the text
        :param color: gray_level of the text, (r,g,b)
        :param y: y position
        :param x: x position (optional)
        :param font: font of the text
        """
        font = pg.font.SysFont(font, font_size)
        t = font.render(text, True, color)
        if x is None:
            x = pg.display.get_surface().get_size()[0] // 2 - t.get_width() // 2
        self.screen.blit(t, (x, y))

    def draw_rect(self, height: int, width: int, gray_level: int, y: int, x: int = None, border_width: int = 2) -> None:
        """
        Draws a rectangle on the current pygame screen. If x is not specified, the text is horizontally centered.
        :param height: height of the rectangle
        :param width: width of the rectangle
        :param gray_level: gray level of the rectangle
        :param y: y position
        :param x: x position (optional)
        :param border_width: width of the border of the rectangle
        """
        if x is None:
            x = pg.display.get_surface().get_size()[0] // 2 - width // 2
        main_color = tuple(gray_level for _ in range(0, 3))
        high_color = tuple(min(gray_level + 50, 255) for _ in range(0, 3))
        low_color = tuple(max(gray_level - 50, 0) for _ in range(0, 3))
        h_b_w = border_width // 2  # half border width
        top_y = y + h_b_w - 1
        bottom_y = y + height - h_b_w - 1
        left_x = x + h_b_w - 1
        right_x = x + width - h_b_w - 1
        pg.draw.rect(self.screen, main_color, pg.Rect(x, y, width, height))
        pg.draw.line(self.screen, high_color, (x, top_y), (right_x, top_y), border_width)
        pg.draw.line(self.screen, high_color, (left_x, y), (left_x, bottom_y), border_width)
        pg.draw.line(self.screen, low_color, (right_x, bottom_y), (right_x, y), border_width)
        pg.draw.line(self.screen, low_color, (right_x + h_b_w, bottom_y), (x, bottom_y), border_width)

    def draw_button(self, text: str, height: int, width: int, gray_level: int, y: int, x: int = None) -> None:
        """
        Draws a button which is a rectangle with a text on it on the current pygame screen.
        :param text: text of the button
        :param height: height of the button
        :param width: width of the button
        :param gray_level: gray level of the button
        :param y: y position
        :param x: x position (optional)
        :return:
        """
        self.draw_rect(height, width, gray_level, y, x)
        self.draw_text(text, height // 2, (0, 0, 0), y + height // 4, x)

    def draw_undiscovered_cell(self, y: int, x: int, flagged: bool = False) -> None:
        """
        Draws an undiscovered cell, which is a rectangle. Puts a flag image on it if flagged.
        :param y: y position
        :param x: x position
        :param flagged: True if the cell is flagged, False otherwise
        """
        self.draw_rect(20, 20, 170, y, x, 2)
        if flagged:
            self.screen.blit(self.flag_img, (x + 1, y + 1))

    def draw_discovered_cell(self, y: int, x: int, value: int) -> None:
        """
        Draws a discovered cell, with the number of bombs around it (blank if 0), a bomb if it's a bomb cell
        :param y: y position
        :param x: x position
        :param value: value of the cell (0-10)
        """
        self.draw_rect(20, 20, 80, y, x, 0)
        self.draw_rect(19, 19, 130, y + 1, x + 1, 0)
        if value == 10:
            pg.draw.rect(self.screen, (200, 0, 0), pg.Rect(x + 1, y + 1, 18, 18))
        if value == 9 or value == 10:
            self.screen.blit(self.bomb_img, (x + 1, y + 1))
        elif value == -3:
            self.screen.blit(self.no_bomb_img, (x + 1, y + 1))
        elif value != 0:
            color = (0, 0, 0)
            match value:
                case 1:
                    color = (0, 1, 253)
                case 2:
                    color = (1, 126, 0)
                case 3:
                    color = (254, 0, 1)
                case 4:
                    color = (1, 0, 130)
                case 5:
                    color = (127, 2, 1)
                case 6:
                    color = (0, 128, 128)
                case 7:
                    color = (0, 0, 0)
                case 8:
                    color = (100, 100, 100)
            self.draw_text(str(value), 16, color, y + 3, x + 5)

    def draw_grid(self):
        """
        Draws the game grid on the current screen
        """
        self.draw_rect(self.grid_height * 20 + 4, self.grid_width * 20 + 4, 170, 68, 18)
        for i in range(0, self.grid_height):
            for j in range(0, self.grid_width):
                if -3 < self.grid.grid[i, j] < 0:
                    self.draw_undiscovered_cell(70 + 20 * i, 20 + 20 * j, self.grid.grid[i, j] == -2)
                else:
                    self.draw_discovered_cell(70 + 20 * i, 20 + 20 * j, self.grid.grid[i, j])

    def draw_timer(self, y: int, x: int) -> None:
        """
        Draws the timer of the game
        :param y: y position
        :param x: x position
        """
        self.timer.update()
        current_time = self.timer.time
        if current_time > 99:
            width = 35 + 15 * int(log10(current_time))
        else:
            width = 65
        text = '00' + str(current_time) if current_time < 10 else ('0' + str(current_time) if current_time < 100 else str(current_time))
        self.draw_rect(40, width, 10, y, x, 0)
        self.draw_text(text, 44, (200, 0, 0), y + 7, x + 5, 'arialbold')

    def draw_remaining_non_flagged_bombs_nb(self, y: int, x: int) -> None:
        """
        Draws the remaining non-flagged bombs number in the grid
        :param y: y position
        :param x: x position
        """
        number = self.grid.get_remaining_non_flagged_bombs_nb()
        text = str(number) if number > 9 else '0' + str(number)
        self.draw_rect(40, 44, 0, y, x)
        self.draw_text(text, 44, (200, 0, 0), y + 7, x + 5, 'arialbold')

    def draw_info_bar(self, game_status: int = 0) -> None:
        """
        Draws the info bar with the timer and remaining bombs
        :param game_status: -1: player lost, 0: currently playing, 1: player won
        """
        self.draw_rect(54, self.grid_width * 20 + 4, 190, 8, 18, 2)
        if self.timer:
            self.draw_timer(15, 25)
        if self.grid:
            self.draw_remaining_non_flagged_bombs_nb(15, 20 + self.grid_width * 20 - 50)
        if game_status == 1:
            self.draw_button("You Won!", 30, 96, 170, 20)
        if game_status == -1:
            self.draw_button("You Lost!", 30, 100, 170, 20)

    def draw_buttons(self):
        """
        Draws all the buttons of the object
        """
        [self.draw_button(btn[1], btn[2], btn[3], 170, btn[4]) for btn in self.buttons]

    def start(self):
        """
        Starts the game by displaying the menu
        """
        self.display_menu()
        self.menu()

    def display_menu(self):
        """
        Displays all the elements of the menu on the current screen (label and buttons)
        """
        self.screen = pg.display.set_mode((400, 400))
        pg.display.set_caption('Minesweeper - Menu')
        self.screen.fill((200, 200, 200))
        self.buttons = [  # [action, value, text, height, width, y]
            [0, "Beginner", 50, 200, 130],
            [1, "Intermediate", 50, 200, 200],
            [2, "Expert", 50, 200, 270],
            [-1, "Quit", 30, 130, 340]
        ]
        self.draw_buttons()
        pg.display.update()

    def menu(self):
        """
        Menu of the game, where the player chooses the difficulty of the game
        """
        screen_width = pg.display.get_surface().get_size()[0]
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    exit()
                elif event.type == pg.MOUSEMOTION or event.type == pg.MOUSEBUTTONDOWN:
                    self.draw_buttons()
                    mouse_pos = pg.mouse.get_pos()
                    x = mouse_pos[0]
                    y = mouse_pos[1]
                    clicked_button = None
                    for btn in self.buttons:
                        if 0 <= x - (screen_width - btn[3]) // 2 <= btn[3] and 0 <= y - btn[4] <= btn[2]:
                            if event.type == pg.MOUSEMOTION:
                                self.draw_button(btn[1], btn[2], btn[3], 120, btn[4])
                            else:
                                self.draw_button(btn[1], btn[2], btn[3], 80, btn[4])
                                clicked_button = btn
                            break
                    if clicked_button:
                        if clicked_button[0] >= 0:
                            self.difficulty = clicked_button[0]
                            if self.difficulty == 0:
                                [self.grid_height, self.grid_width, self.bombs_nb] = [9, 9, 10]
                            elif self.difficulty == 1:
                                [self.grid_height, self.grid_width, self.bombs_nb] = [16, 16, 40]
                            else:
                                [self.grid_height, self.grid_width, self.bombs_nb] = [16, 30, 99]
                            self.grid = Grid(self.grid_height, self.grid_width, self.bombs_nb)
                            self.display_game()
                            break
                        else:
                            exit()
                    pg.display.update()
            else:
                continue
            break
        self.play_game()

    def display_game(self) -> None:
        """
        Displays the components of the game and creates a new screen instance
        """
        screen = pg.display.set_mode((self.grid_width * 20 + 40, self.grid_height * 20 + 40 + 50))
        pg.display.set_caption(
            f'Minesweeper - {"Beginner" if self.difficulty == 0 else "Intermediate" if self.difficulty == 1 else "Expert"}'
        )
        screen.fill((200, 200, 200))
        self.draw_grid()
        self.draw_info_bar()
        pg.display.update()

    def play_game(self) -> None:
        """
        Main game loop
        """
        self.timer = Timer()
        while True:
            if self.grid.game_status == 0:
                self.draw_timer(15, 25)
            for event in pg.event.get():
                if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                    exit()
                if event.type == pg.KEYDOWN and event.key == pg.K_r:
                    self.display_menu()
                    self.menu()
                    break
                if event.type == pg.MOUSEBUTTONDOWN and self.grid.game_status == 0:
                    mouse_pos = pg.mouse.get_pos()
                    x = mouse_pos[0]
                    y = mouse_pos[1]

                    if 20 <= x <= 20 + 20 * self.grid_width and 70 <= y <= 70 + 20 * self.grid_height:
                        cell_x = (x - 20) // 20
                        cell_y = (y - 70) // 20
                        if event.button == 1:  # left click
                            self.grid.discover_cell((cell_y, cell_x))
                        elif event.button == 3:  # right click
                            self.grid.flag_cell((cell_y, cell_x))
                            self.draw_remaining_non_flagged_bombs_nb(15, 20 + self.grid_width * 20 - 50)
                        self.draw_grid()
                    if self.grid.game_status != 0:
                        self.draw_info_bar(self.grid.game_status)
                        pg.display.update()
            pg.display.update()
