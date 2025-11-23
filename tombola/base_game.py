from abc import ABC, abstractmethod

class BaseGame(ABC):
    """Interfaz general para cualquier juego de lotería."""

    @abstractmethod
    def draw(self):
        """Devuelve un sorteo aleatorio según las reglas del juego."""
        pass

    @abstractmethod
    def num_range(self):
        """Devuelve el rango total de números válidos del juego."""
        pass

    @abstractmethod
    def picks(self):
        """Devuelve cuántos números se sortean."""
        pass
