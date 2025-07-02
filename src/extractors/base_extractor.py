from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """
    Classe base abstrata para todos os extratores de serviços da AWS.
    Define um contrato que força todas as classes filhas a implementarem
    o método 'extract'.
    """

    @abstractmethod
    def extract(self, aws_session):
        """
        Método abstrato para extrair dados de um serviço da AWS.
        Deve ser implementado por cada extrator de serviço específico.

        :param aws_session: A sessão do boto3 já configurada com as credenciais.
        :return: Um dicionário onde as chaves são nomes de abas (sheets) e os
                 valores são listas de dicionários com os dados extraídos.
        """
        pass