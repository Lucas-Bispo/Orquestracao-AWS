import boto3
from botocore.exceptions import ProfileNotFound

class AWSConnector:
    """
    Gerencia a criação da sessão com a AWS de forma segura,
    utilizando perfis da AWS CLI.
    """
    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.session = None

    def get_session(self):
        """
        Cria e retorna um objeto de sessão do boto3.
        Lança uma exceção se o perfil não for encontrado.
        """
        try:
            print(f"Iniciando sessão na AWS com o perfil: '{self.profile_name}'...")
            self.session = boto3.Session(profile_name=self.profile_name)
            
            # Testa a identidade para validar as credenciais
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"Sessão estabelecida com sucesso para a conta: {identity['Account']}")
            
            return self.session
        except ProfileNotFound:
            print(f"ERRO: O perfil AWS '{self.profile_name}' não foi encontrado.")
            print("Por favor, configure-o usando 'aws configure --profile {}'".format(self.profile_name))
            raise
        except Exception as e:
            print(f"ERRO ao tentar estabelecer sessão com a AWS: {e}")
            raise