from abc import ABC, abstractmethod

class BaseScraper(ABC):
    """
    Classe base abstrata para scrapers de ofertas.
    """
    @abstractmethod
    def fetch_deals(self):
        """
        Método abstrato para buscar ofertas.
        Deve ser implementado por todas as subclasses.
        """
        pass
