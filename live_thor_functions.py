import numpy as np
from io import BytesIO
import imageio
import cv2


# изначальный класс
class LiveField:
    """
    Класс для моделирования игры "Жизнь на торе".
    """
    def __init__(self, n: int, m: int, start_field: list = None):
        """
        Инициализация начальное поля для игры
        n : int -- количество строк (если start_field не задан).
        m : int -- количество столбцов (если start_field не задан).
        start_field : list -- двумерный список (список списков)
        """
        if (start_field is not None):
            self._row = len(start_field)
            self._col = len(start_field[0])
            self._field = np.array(start_field, dtype=bool)
            self._next_field = None
            return
        self._field = np.zeros((n, m), dtype=bool)
        self._row = n
        self._col = m
        self._next_field = None
    
    def reverse_cell(self, i: int, j: int):
        """
        Инвертирует состояние клетки (i, j).
        i : int -- индекс строки.
        j : int -- индекс столбца.
        """
        self._field[i, j] = not self._field[i, j]
    
    def _count_neighbors(self):
        """.
        Подсчитывает количество живых соседей для каждой клетки.
        return: np.ndarray(int)
        """
        g = self._field.astype(int)
        neighbors = sum(
            np.roll(g, (dx, dy), axis=(0, 1))
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if (dx, dy) != (0, 0)
        )
        return neighbors
    
    def next_state(self):
        """
        Вычисляет следующее состояние поля.
        return: np.ndarray(bool)
        """
        if self._next_field is not None:
            return np.copy(self._next_field)
        neighbors = self._count_neighbors()
        new_field = (neighbors == 3) | (self._field & (neighbors == 2))
        self._next_field = np.copy(new_field)
        return new_field
    
    def update(self):
        """
        Переводит поле в следующее состояние.
        """
        self._field = self.next_state()
        self._next_field = None


def random_field(H: int, W: int, p: float) -> np.ndarray:
    """
    Генерируем случайное булево поле размера H x W,
    где каждая клетка жива с вероятностью p.
    H : int -- количество строк.
    W : int -- количество столбцов.
    p : float -- вероятность жизни (0 < p < 1).

    return: np.ndarray(bool)
    """
    rand = np.random.rand(H, W)
    return rand < p

def get_frames(n: int, start_frame: list) -> list:
    """
    Из стартого значения поля генерируем n следующих
    n : int -- количесво требуемых фреймов
    
    return: list[np.ndarray(bool)]
    """
    sf = np.array(start_frame, dtype=bool)
    frames = [np.array(sf)]
    generator = LiveField(*sf.shape, sf)
    for _ in range(n - 1):
        frames.append(generator.next_state())
        generator.update()
    return frames

def resize_frames(frames, target_size=(512, 512)):
    """
    Изменяет размер каждого кадра до target_size (width, height)
    frames: list[ndarray(bool)]
    target_size: tuple(new_width: int, new_height: int)
    
    return: lis[ndarray(int)]
    """
    resized = []
    for frame in frames:
        frame_uint8 = frame.astype(np.uint8) * 255
        frame_resized = cv2.resize(frame_uint8, target_size, interpolation=cv2.INTER_NEAREST)
        resized.append(frame_resized)
    return resized

def generate_gif(frames, output, fps = 4):
    """
    Генерирует гифку из списка кадров.
    frames: list[ndarray(int)]
    output: BytesIO -- объект для сохранения гифки
    fps: int -- количество кадров в секунду
    
    return: None
    """
    imageio.mimwrite(output, frames, format='GIF', fps=fps)

def generate_gif_from_start(start_frame, n_frames=80, fps=4):
    """Генерирует гифку из заданного начального поля.
    start_frame: list -- начальное поле (двумерный список)
    n_frames: int -- количество кадров в гифке
    filename: str -- имя файла для сохранения гифки
    fps: int -- количество кадров в секунду
    
    return: bytes -- байты с гифкой
    """
    frames = get_frames(n_frames, start_frame)
    resized_frames = resize_frames(frames)
    output = BytesIO()
    generate_gif(resized_frames, output, fps)
    return output.getvalue()

def generate_gif_from_random(H, W, p, n_frames=80, fps=4):
    start_frame = random_field(H, W, p)
    frames = get_frames(n_frames, start_frame)
    resized_frames = resize_frames(frames)
    output = BytesIO()
    generate_gif(resized_frames, output, fps)
    return output.getvalue()