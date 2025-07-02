import pandas as pd
import os

class ReportGenerator:
    """
    Responsável por pegar todos os dados extraídos e gerar um único
    relatório consolidado em formato Excel (.xlsx).
    """

    def __init__(self, client_name):
        self.client_name = client_name
        self.output_path = os.path.join('clients', self.client_name, 'output')
        self.filename = os.path.join(self.output_path, f'{self.client_name}_aws_report.xlsx')
        # A ordem das abas é definida aqui!
        self.sheet_order = [
            'IAM_Users',
            'IAM_Roles',
            # Futuras abas de VPC virão aqui
            # 'VPCs',
            # 'Subnets',
            # 'Route_Tables',
            # Futuras abas de EC2 virão depois
            # 'EC2_Instances'
        ]

    def generate_excel(self, all_data):
        """
        Cria o arquivo Excel com múltiplas abas na ordem definida.

        :param all_data: Um dicionário contendo todos os dados coletados pelos extratores.
                         Ex: {'IAM_Users': [...], 'IAM_Roles': [...]}
        """
        print(f"Gerando relatório Excel em: {self.filename}")
        
        # Garante que o diretório de output exista
        os.makedirs(self.output_path, exist_ok=True)

        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            # Escreve as abas na ordem definida
            for sheet_name in self.sheet_order:
                if sheet_name in all_data and all_data[sheet_name]:
                    print(f"  - Escrevendo aba: {sheet_name}...")
                    df = pd.DataFrame(all_data[sheet_name])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Escreve quaisquer outras abas que não estavam na ordem definida
            for sheet_name, data in all_data.items():
                if sheet_name not in self.sheet_order and data:
                    print(f"  - Escrevendo aba extra: {sheet_name}...")
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print("Relatório Excel gerado com sucesso!")