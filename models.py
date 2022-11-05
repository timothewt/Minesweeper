import random
import time
from math import log10
import pygame
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
            self.game_ended = False
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
            self.game_ended = True
        if current_cell_bombs == 0:  # if there are no bombs near, discovers all its neighbours
            neighbours = self.get_neighbours(cell_coordinates)
            undiscovered_neighbours = [neighbour for neighbour in neighbours if self.grid[neighbour] == -1]
            for neighbour in undiscovered_neighbours:
                self.discover_cell(neighbour)

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

    def has_discovered_all_non_bombs_cells(self) -> bool:
        """
        Counts the remaining undiscovered cells and compares it to the number of bombs
        :return: True if the player discovered all the non-bombs cells, False otherwise
        """
        non_discovered_cells = self.grid < 0  # -1 for non-flagged bombs, -2 for flagged bombs
        return np.count_nonzero(non_discovered_cells) == self.bombs_nb

    def has_discovered_bomb_cell(self) -> bool:
        """
        Checks if there is a bomb cell discovered
        :return: True if a bomb has been discovered, False otherwise
        """
        return 9 in self.grid


class Timer:
    def __init__(self):
        self.start = time.time()
        self.time = 0

    def __str__(self):
        return f"Elapsed time: {self.time}s"

    def update(self):
        self.time = int(time.time() - self.start)


class MenuGUI:
    def __init__(self):
        self.screen_width = 400
        self.screen_height = 400
        self.difficulty = 0

    def draw_centered_text(self, screen: pygame.Surface, text: str, font_size: int, y_pos: int) -> None:
        font = pygame.font.SysFont('gothambold', font_size)
        t = font.render(text, True, (0, 0, 0))
        screen.blit(t, (self.screen_width // 2 - t.get_width() // 2, y_pos))

    def draw_centered_rect(self, screen: pygame.Surface, height: int, width: int, y_pos: int) -> None:
        x_pos = (self.screen_width - width) // 2
        pygame.draw.line(screen, (180, 180, 180), (x_pos, y_pos), (x_pos + width, y_pos), 3)
        pygame.draw.line(screen, (180, 180, 180), (x_pos, y_pos), (x_pos, y_pos + height), 3)
        pygame.draw.line(screen, (80, 80, 80), (x_pos + width, y_pos + height), (x_pos + width, y_pos), 3)
        pygame.draw.line(screen, (80, 80, 80), (x_pos + width, y_pos + height), (x_pos, y_pos + height), 3)
        pygame.draw.rect(screen, (130, 130, 130), pygame.Rect(x_pos, y_pos, width, height))

    def draw_centered_rect_dark(self, screen: pygame.Surface, height: int, width: int, y_pos: int) -> None:
        x_pos = (self.screen_width - width) // 2
        pygame.draw.line(screen, (150, 150, 150), (x_pos, y_pos), (x_pos + width, y_pos), 3)
        pygame.draw.line(screen, (150, 150, 150), (x_pos, y_pos), (x_pos, y_pos + height), 3)
        pygame.draw.line(screen, (50, 50, 50), (x_pos + width, y_pos + height), (x_pos + width, y_pos), 3)
        pygame.draw.line(screen, (50, 50, 50), (x_pos + width, y_pos + height), (x_pos, y_pos + height), 3)
        pygame.draw.rect(screen, (100, 100, 100), pygame.Rect(x_pos, y_pos, width, height))

    def draw_button(self, screen: pygame.Surface, text: str, height: int, width: int, y_pos: int) -> None:
        self.draw_centered_rect(screen, height, width, y_pos)
        self.draw_centered_text(screen, text, height // 2, y_pos + height // 4)

    def draw_hovered_button(self, screen: pygame.Surface, text: str, height: int, width: int, y_pos: int) -> None:
        self.draw_centered_rect_dark(screen, height, width, y_pos)
        self.draw_centered_text(screen, text, height // 2, y_pos + height // 4)

    def draw_button_list(self, screen: pygame.Surface, buttons: list[str | int | str | int | int | int]):
        for button in buttons:
            self.draw_button(screen, button[2], button[3], button[4], button[5])

    def display(self):
        pygame.init()
        screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Minesweeper - Menu')
        screen.fill((200, 200, 200))

        buttons = [  # [action, value, text, height, width, y_pos]
            ["start", 0, "Beginner", 50, 200, 130],
            ["start", 1, "Intermediate", 50, 200, 200],
            ["start", 2, "Expert", 50, 200, 270],
            ["quit", -1, "Quit", 30, 130, 340]
        ]

        self.draw_centered_text(screen, "Minesweeper", 50, 30)
        self.draw_button_list(screen, buttons)

        pygame.display.update()

        while True:  # displays the window until the player picks a difficulty or leaves the game
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    exit()
                if event.type == pygame.MOUSEMOTION:
                    self.draw_button_list(screen, buttons)
                    mouse_pos = pygame.mouse.get_pos()
                    x = mouse_pos[0]
                    y = mouse_pos[1]
                    for button in buttons:
                        if 0 <= x - (self.screen_width - button[4]) // 2 <= button[4] and 0 <= y - button[5] <= button[3]:
                            self.draw_hovered_button(screen, button[2], button[3], button[4], button[5])
                            break
                    pygame.display.update()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    x = mouse_pos[0]
                    y = mouse_pos[1]
                    clicked_button = None
                    for button in buttons:
                        if 0 <= x - (self.screen_width - button[4]) // 2 <= button[4] and 0 <= y - button[5] <= button[3]:
                            clicked_button = button
                            break
                    if clicked_button:
                        if clicked_button[0] == "start":
                            self.difficulty = clicked_button[1]
                            pygame.display.quit()
                            break
                        else:
                            exit()
            else:
                continue
            break


class GameGUI:
    def __init__(self):
        self.difficulty = 0
        self.grid_width = 0
        self.grid_height = 0
        self.bombs_nb = 0
        self.grid = None
        self.flag_img = None
        self.bomb_img = None
        self.no_bomb_img = None
        self.timer = None

    def draw_undiscovered_cell(self, screen: pygame.Surface, x: int, y: int, flagged: bool = False):
        pygame.draw.line(screen, (220, 220, 220), (x + 1, y + 1), (x + 20, y + 1), 2)
        pygame.draw.line(screen, (220, 220, 220), (x + 1, y + 1), (x + 1, y + 20), 2)
        pygame.draw.line(screen, (120, 120, 120), (x + 19, y + 19), (x + 19, y + 1), 2)
        pygame.draw.line(screen, (120, 120, 120), (x + 19, y + 19), (x + 1, y + 19), 2)
        pygame.draw.rect(screen, (170, 170, 170), pygame.Rect(x + 2, y + 2, 16, 16))
        if flagged:
            screen.blit(self.flag_img, (x + 1, y + 1))

    def draw_discovered_cell(self, screen: pygame.Surface, x: int, y: int, value: int):
        pygame.draw.rect(screen, (130, 130, 130), pygame.Rect(x + 1, y + 1, 18, 18))
        pygame.draw.rect(screen, (80, 80, 80), pygame.Rect(x, y, 20, 20), 1)
        if value == 10:
            pygame.draw.rect(screen, (200, 0, 0), pygame.Rect(x + 1, y + 1, 18, 18))
        if value == 9 or value == 10:
            screen.blit(self.bomb_img, (x + 1, y + 1))
        elif value == -3:
            screen.blit(self.no_bomb_img, (x + 1, y + 1))
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
                    color = (128, 128, 128)
            font = pygame.font.SysFont('gothambold', 16)
            t = font.render(str(value), True, color)
            screen.blit(t, (x + 10 - t.get_width() // 2, y + 3))

    def draw_grid(self, screen: pygame.Surface):
        pygame.draw.line(screen, (220, 220, 220), (18, 68), (18 + self.grid_width * 20 + 4, 68), 2)
        pygame.draw.line(screen, (220, 220, 220), (18, 68), (18, 68 + self.grid_height * 20 + 4), 2)
        pygame.draw.line(screen, (120, 120, 120), (18 + self.grid_width * 20 + 4, 68 + self.grid_height * 20 + 4), (18 + self.grid_width * 20 + 4, 68), 2)
        pygame.draw.line(screen, (120, 120, 120), (18 + self.grid_width * 20 + 4, 68 + self.grid_height * 20 + 4), (18, 68 + self.grid_height * 20 + 4), 2)
        pygame.draw.rect(screen, (200, 200, 200), (20, 70, self.grid_width * 20, self.grid_height * 20))
        for i in range(0, self.grid_height):
            for j in range(0, self.grid_width):
                if -3 < self.grid.grid[i, j] < 0:
                    self.draw_undiscovered_cell(screen, 20 + 20 * j, 70 + 20 * i, self.grid.grid[i, j] == -2)
                else:
                    self.draw_discovered_cell(screen, 20 + 20 * j, 70 + 20 * i, self.grid.grid[i, j])

    def draw_menu_bar(self, screen: pygame.Surface):
        pygame.draw.line(screen, (220, 220, 220), (18, 8), (18 + self.grid_width * 20 + 4, 8), 2)
        pygame.draw.line(screen, (220, 220, 220), (18, 8), (18, 8 + 50 + 4), 2)
        pygame.draw.line(screen, (120, 120, 120), (18 + self.grid_width * 20 + 4, 8 + 50 + 4), (18 + self.grid_width * 20 + 4, 8), 2)
        pygame.draw.line(screen, (120, 120, 120), (18 + self.grid_width * 20 + 4, 8 + 50 + 4), (18, 8 + 50 + 4), 2)
        bg_color = (170, 170, 170)
        if self.grid.game_ended:
            if self.grid.has_discovered_all_non_bombs_cells():
                bg_color = (0, 160, 0)
            else:
                bg_color = (160, 0, 0)
        pygame.draw.rect(screen, bg_color, pygame.Rect(20, 10, self.grid_width * 20, 50))
        self.draw_timer(screen)
        self.draw_remaining_non_flagged_bombs(screen)

    def draw_timer(self, screen: pygame.Surface):
        self.timer.update()
        current_time = self.timer.time
        if current_time > 99:
            timer_width = 35 + 15 * int(log10(current_time))
        else:
            timer_width = 65
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(25, 15, timer_width, 40))
        font = pygame.font.SysFont('arialbold', 50)
        timer_text = str(current_time)
        if current_time < 10:
            timer_text = '00' + timer_text
        elif current_time < 100:
            timer_text = '0' + timer_text
        t = font.render(timer_text, True, (200, 0, 0))
        screen.blit(t, (25 + timer_width // 2 - t.get_width() // 2, 15 + 4))

    def draw_remaining_non_flagged_bombs(self, screen: pygame.Surface):
        remaining_non_flagged_bombs = self.grid.get_remaining_non_flagged_bombs_nb()
        string = str(remaining_non_flagged_bombs) if remaining_non_flagged_bombs > 9 else '0' + str(remaining_non_flagged_bombs)
        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(20 + self.grid_width * 20 - 50 - 5, 15, 50, 40))
        font = pygame.font.SysFont('arialbold', 50)
        text = font.render(string, True, (200, 0, 0))
        screen.blit(text, (20 + self.grid_width * 20 - 25 - 5 - text.get_width() // 2, 15 + 4))

    def display(self):
        pygame.init()
        screen = pygame.display.set_mode((self.grid_width * 20 + 40, self.grid_height * 20 + 40 + 50))
        pygame.display.set_caption(
            f'Minesweeper - In-Game - {"Beginner" if self.difficulty == 0 else "Intermediate" if self.difficulty == 1 else "Expert"}')
        screen.fill((200, 200, 200))

        self.flag_img = pygame.image.load("assets/flag.png")
        self.bomb_img = pygame.image.load("assets/bomb.png")
        self.no_bomb_img = pygame.image.load("assets/no_bomb.png")
        self.timer = Timer()

        self.draw_grid(screen)
        self.draw_menu_bar(screen)
        pygame.display.update()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and not self.grid.game_ended:
                    mouse_pos = pygame.mouse.get_pos()
                    x = mouse_pos[0]
                    y = mouse_pos[1]

                    if 20 <= x <= 20 + 20 * self.grid_width and 70 <= y <= 70 + 20 * self.grid_height:
                        cell_x = (x - 20) // 20
                        cell_y = (y - 70) // 20
                        if event.button == 1:  # left click
                            self.grid.discover_cell((cell_y, cell_x))
                            if self.grid.has_discovered_all_non_bombs_cells():
                                self.grid.flag_non_flagged_bombs()
                                self.grid.game_ended = True
                        elif event.button == 3:  # right click
                            self.grid.flag_cell((cell_y, cell_x))
                            self.draw_remaining_non_flagged_bombs(screen)
                        self.draw_grid(screen)
            if self.grid.game_ended:
                self.draw_menu_bar(screen)
                pygame.display.update()
                while True:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                            exit()
                        elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                            self.start_game()
                            break
                    else:
                        continue
                    break
            else:
                self.draw_timer(screen)
            pygame.display.update()

    def start_game(self):
        self.grid = Grid(self.grid_height, self.grid_width, self.bombs_nb)
        self.timer = Timer()
        self.display()


class Game:
    def __init__(self):
        self.menu_gui = MenuGUI()
        self.game_gui = GameGUI()
        self.difficulty = 0

    def start_game(self):
        self.menu_gui.display()
        self.difficulty = self.menu_gui.difficulty
        self.game_gui.difficulty = self.difficulty
        if self.difficulty == 0:
            [self.game_gui.grid_height, self.game_gui.grid_width, self.game_gui.bombs_nb] = [9, 9, 10]
        elif self.difficulty == 1:
            [self.game_gui.grid_height, self.game_gui.grid_width, self.game_gui.bombs_nb] = [16, 16, 40]
        else:
            [self.game_gui.grid_height, self.game_gui.grid_width, self.game_gui.bombs_nb] = [16, 30, 99]
        self.game_gui.start_game()
