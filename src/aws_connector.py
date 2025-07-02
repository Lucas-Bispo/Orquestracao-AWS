# src/aws_connector.py

import boto3
from botocore.exceptions import ClientError

class AWSConnector:
    """
    Gerencia a criação da sessão com a AWS de forma direta,
    utilizando as credenciais fornecidas em tempo de execução.
    """
    def __init__(self, aws_access_key_id, aws_secret_access_key, region_name):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.region_name = region_name
        self.session = None

    def get_session(self):
        """
        Cria e retorna um objeto de sessão do boto3 usando as credenciais diretas.
        Lança uma exceção se as credenciais forem inválidas.
        """
        try:
            print(f"Iniciando sessão na AWS com as credenciais fornecidas na região '{self.region_name}'...")
            self.session = boto3.Session(
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
            
            # Testa a identidade para validar as credenciais
            sts_client = self.session.client('sts')
            identity = sts_client.get_caller_identity()
            print(f"Sessão estabelecida com sucesso para a conta: {identity['Account']}")
            
            return self.session
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidClientTokenId':
                print("ERRO: O AWS Access Key ID fornecido não é válido.")
            elif e.response['Error']['Code'] == 'SignatureDoesNotMatch':
                print("ERRO: O AWS Secret Access Key fornecido não corresponde ao Access Key ID.")
            else:
                print(f"ERRO de cliente ao tentar estabelecer sessão com a AWS: {e}")
            raise
        except Exception as e:
            print(f"ERRO inesperado ao tentar estabelecer sessão com a AWS: {e}")
            raise