import os
from dotenv import load_dotenv

# Importando as classes que criamos
from src.aws_connector import AWSConnector
from src.extractors.iam_extractor import IAMExtractor
from src.report_generator import ReportGenerator

def run_analysis(client_name, aws_profile):
    """
    Função principal que orquestra a análise para um cliente.
    """
    print("-" * 50)
    print(f"Iniciando orquestração para o cliente: {client_name}")
    print("-" * 50)

    try:
        # 1. Conectar à AWS
        connector = AWSConnector(profile_name=aws_profile)
        aws_session = connector.get_session()

        # 2. Preparar extratores e coletar dados
        extractors = [IAMExtractor()]
        all_extracted_data = {}

        for extractor in extractors:
            data = extractor.extract(aws_session)
            all_extracted_data.update(data)

        # 3. Gerar o Relatório
        if not all_extracted_data:
            print("Nenhum dado foi extraído. O relatório não será gerado.")
            return

        report_gen = ReportGenerator(client_name=client_name)
        report_gen.generate_excel(all_extracted_data)
        
        print("-" * 50)
        print("Orquestração finalizada com sucesso!")
        print("-" * 50)

    except Exception as e:
        print(f"\nOcorreu um erro fatal durante a orquestração: {e}")


if __name__ == "__main__":
    # Carrega as variáveis do arquivo .env para o ambiente
    load_dotenv()

    # Puxa as variáveis do ambiente usando os.getenv()
    CLIENTE_EXEMPLO = os.getenv("CLIENTE_EXEMPLO")
    PERFIL_AWS_EXEMPLO = os.getenv("PERFIL_AWS_EXEMPLO")

    # Verificação para garantir que as variáveis foram carregadas
    if not CLIENTE_EXEMPLO or not PERFIL_AWS_EXEMPLO:
        print("ERRO: As variáveis CLIENTE_EXEMPLO e PERFIL_AWS_EXEMPLO não foram encontradas.")
        print("Por favor, crie um arquivo .env na raiz do projeto e defina essas variáveis.")
    else:
        # Cria a estrutura de pastas manualmente para o primeiro teste
        os.makedirs(os.path.join('clients', CLIENTE_EXEMPLO, 'output'), exist_ok=True)
        
        # Executa a análise com as variáveis carregadas do .env
        run_analysis(client_name=CLIENTE_EXEMPLO, aws_profile=PERFIL_AWS_EXEMPLO)