import os
import sys
import getpass

# Importando as classes que criamos
from src.aws_connector import AWSConnector
from src.extractors.iam_extractor import IAMExtractor
from src.report_generator import ReportGenerator

def run_analysis(client_name, aws_access_key_id, aws_secret_access_key, region_name):
    """
    Função principal que orquestra a análise para um cliente.
    """
    print("-" * 50)
    print(f"Iniciando orquestração para o cliente: {client_name}")
    print("-" * 50)

    try:
        # 1. Conectar à AWS com as credenciais fornecidas
        connector = AWSConnector(
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name
        )
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
        print(f"Relatório salvo em: clients/{client_name}/output/")
        print("-" * 50)

    except Exception as e:
        print(f"\nOcorreu um erro fatal durante a orquestração: {e}")
        sys.exit(1)


if __name__ == "__main__":
    
    print("=" * 50)
    print("      Ferramenta de Orquestração e Análise AWS")
    print("         (Modo de Credenciais Diretas)")
    print("=" * 50)

    try:
        # 1. Pergunta o nome do cliente
        client_name_input = input("Digite o nome do cliente (ex: EmpresaX): ")

        # 2. Pergunta as credenciais de forma interativa
        access_key_input = input("Digite seu AWS Access Key ID: ")
        secret_key_input = getpass.getpass("Digite seu AWS Secret Access Key: ") # A digitação ficará oculta
        region_input = input("Digite a Região da AWS (ex: us-east-1): ")

        if not all([client_name_input, access_key_input, secret_key_input, region_input]):
            print("\nERRO: Todos os campos (cliente, chaves e região) são obrigatórios.")
            sys.exit(1)

        # Cria a estrutura de pastas para o cliente
        os.makedirs(os.path.join('clients', client_name_input, 'output'), exist_ok=True)
        
        # Executa a análise com os dados fornecidos pelo usuário
        run_analysis(
            client_name=client_name_input,
            aws_access_key_id=access_key_input,
            aws_secret_access_key=secret_key_input,
            region_name=region_input
        )

    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário. Encerrando.")
        sys.exit(0)