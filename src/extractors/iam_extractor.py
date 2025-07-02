from .base_extractor import BaseExtractor

class IAMExtractor(BaseExtractor):
    """
    Extrai informações de usuários e roles do AWS IAM.
    """
    def extract(self, aws_session):
        print("Iniciando extração de dados do IAM...")
        client = aws_session.client('iam')
        
        # Dicionário para armazenar todos os dados do IAM
        iam_data = {}

        # 1. Extrair Usuários
        users_list = []
        paginator = client.get_paginator('list_users')
        for page in paginator.paginate():
            for user in page['Users']:
                users_list.append({
                    'UserName': user.get('UserName'),
                    'UserId': user.get('UserId'),
                    'Arn': user.get('Arn'),
                    'CreateDate': user.get('CreateDate').strftime('%Y-%m-%d %H:%M:%S'),
                    'PasswordLastUsed': user.get('PasswordLastUsed', 'N/A')
                })
        iam_data['IAM_Users'] = users_list
        print(f"  - {len(users_list)} usuários encontrados.")

        # 2. Extrair Roles
        roles_list = []
        paginator = client.get_paginator('list_roles')
        for page in paginator.paginate():
            for role in page['Roles']:
                # Simplificando a política de confiança para melhor visualização
                trust_policy = role.get('AssumeRolePolicyDocument', {})
                principal = trust_policy.get('Statement', [{}])[0].get('Principal', 'N/A')

                roles_list.append({
                    'RoleName': role.get('RoleName'),
                    'RoleId': role.get('RoleId'),
                    'Arn': role.get('Arn'),
                    'CreateDate': role.get('CreateDate').strftime('%Y-%m-%d %H:%M:%S'),
                    'Description': role.get('Description', 'N/A'),
                    'TrustedPrincipal': str(principal) # Converte o principal para string
                })
        iam_data['IAM_Roles'] = roles_list
        print(f"  - {len(roles_list)} roles encontradas.")

        print("Extração do IAM concluída.")
        return iam_data