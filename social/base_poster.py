from abc import ABC, abstractmethod

class BasePoster(ABC):
    """
    Classe base abstrata para postagem em redes sociais.
    """
    @abstractmethod
    def post_deal(self, deal_data):
        """
        Método abstrato para postar uma oferta.
        Deve ser implementado por todas as subclasses.
        """
        pass
