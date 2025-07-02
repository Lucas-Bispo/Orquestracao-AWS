import sys
from datetime import datetime, timezone
from .base_extractor import BaseExtractor

class IAMExtractor(BaseExtractor):
    """
    Extrai informações detalhadas de usuários do AWS IAM, incluindo
    status de senha, chaves de acesso, MFA, grupos e políticas herdadas.
    """
    def extract(self, aws_session):
        iam_client = aws_session.client('iam')
        users_details = []
        
        try:
            paginator = iam_client.get_paginator('list_users')
            all_users = []
            print("Iniciando extração detalhada de dados do IAM (isso pode levar alguns minutos)...")
            
            # Primeiro, coleta todos os usuários para ter um total
            for page in paginator.paginate():
                all_users.extend(page['Users'])
            
            total_users = len(all_users)
            print(f"Encontrados {total_users} usuários. Coletando detalhes de cada um...")

            # Processa cada usuário para obter os detalhes completos
            for i, user in enumerate(all_users):
                username = user['UserName']
                # Imprime o progresso para o usuário
                progress = f"  - Processando usuário {i + 1}/{total_users}: {username}"
                print(progress, end='\r') # O '\r' faz a linha ser reescrita
                
                details = self._get_user_details(user, iam_client)
                users_details.append(details)

            print("\nExtração detalhada do IAM concluída.") # Pula uma linha após a barra de progresso
            # Retorna os dados em uma nova aba chamada 'IAM_Users_Detailed'
            return {'IAM_Users_Detailed': users_details}

        except Exception as e:
            print(f"\nERRO ao extrair dados do IAM: {e}")
            return {}

    def _get_user_details(self, user, iam_client):
        """Função auxiliar para coletar os múltiplos pontos de dados de um único usuário."""
        username = user['UserName']
        now = datetime.now(timezone.utc)
        
        # Objeto base com valores padrão
        details = {
            'UserName': username,
            'ARN': user['Arn'],
            'Path': user['Path'],
            'CreationTime': user['CreateDate'].strftime('%Y-%m-%d %H:%M:%S'),
            'ConsoleAccess': 'Disabled',
            'PasswordAge (days)': 'N/A',
            'ConsoleLastSignIn': 'N/A',
            'MFA': 'Disabled',
            'AccessKeyId': 'N/A',
            'AccessKeyActive': 'N/A',
            'AccessKeyAge (days)': 'N/A',
            'AccessKeyLastUsed': 'N/A',
            'Groups': 'N/A',
            'GroupPolicies': 'N/A',
            'SigningCerts': 0,
            'LastActivity (days)': 'N/A'
        }

        # 1. Informações de Senha e Console
        try:
            login_profile = iam_client.get_login_profile(UserName=username)
            details['ConsoleAccess'] = 'Enabled'
            password_create_date = login_profile['LoginProfile']['CreateDate']
            details['PasswordAge (days)'] = (now - password_create_date).days
        except iam_client.exceptions.NoSuchEntityException:
            # É normal um usuário não ter senha (ex: usuário de serviço)
            pass

        if user.get('PasswordLastUsed'):
            details['ConsoleLastSignIn'] = user['PasswordLastUsed'].strftime('%Y-%m-%d %H:%M:%S')
            
        # 2. Informações de MFA (Multi-Factor Authentication)
        mfa_devices = iam_client.list_mfa_devices(UserName=username)['MFADevices']
        if mfa_devices:
            details['MFA'] = 'Enabled'

        # 3. Informações de Chaves de Acesso (Access Keys)
        keys_metadata = iam_client.list_access_keys(UserName=username)['AccessKeyMetadata']
        if keys_metadata:
            # Pegando a chave mais recente para o relatório (uma conta pode ter duas)
            latest_key = sorted(keys_metadata, key=lambda k: k['CreateDate'], reverse=True)[0]
            key_id = latest_key['AccessKeyId']
            details['AccessKeyId'] = key_id
            details['AccessKeyActive'] = latest_key['Status']
            details['AccessKeyAge (days)'] = (now - latest_key['CreateDate']).days
            
            try:
                last_used_info = iam_client.get_access_key_last_used(AccessKeyId=key_id)['AccessKeyLastUsed']
                if 'LastUsedDate' in last_used_info:
                    details['AccessKeyLastUsed'] = last_used_info['LastUsedDate'].strftime('%Y-%m-%d %H:%M:%S')
                else:
                    details['AccessKeyLastUsed'] = 'Never used'
            except Exception:
                details['AccessKeyLastUsed'] = 'Error fetching use'
                
        # 4. Informações de Grupos e Políticas herdadas
        groups_paginator = iam_client.get_paginator('list_groups_for_user')
        user_groups = []
        user_policies = []
        for page in groups_paginator.paginate(UserName=username):
            for group in page['Groups']:
                group_name = group['GroupName']
                user_groups.append(group_name)
                # Pega políticas gerenciadas (managed)
                attached_policies = iam_client.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
                for policy in attached_policies:
                    user_policies.append(f"{group_name} -> {policy['PolicyName']} (Managed)")
                # Pega políticas em linha (inline)
                inline_policies = iam_client.list_group_policies(GroupName=group_name)['PolicyNames']
                for policy_name in inline_policies:
                    user_policies.append(f"{group_name} -> {policy_name} (Inline)")
        
        if user_groups:
            details['Groups'] = ', '.join(user_groups)
        if user_policies:
            details['GroupPolicies'] = '; '.join(user_policies)
            
        # 5. Informações de Certificados de Assinatura
        certs = iam_client.list_signing_certificates(UserName=username)['Certificates']
        details['SigningCerts'] = len(certs)
        
        # 6. Cálculo da Última Atividade
        last_pass_used = user.get('PasswordLastUsed')
        last_key_used_str = details.get('AccessKeyLastUsed')
        last_key_used = None
        if last_key_used_str and ' ' in last_key_used_str:
            last_key_used = datetime.strptime(last_key_used_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            
        last_activity_date = max(d for d in [last_pass_used, last_key_used] if d is not None)
        if last_activity_date:
            details['LastActivity (days)'] = (now - last_activity_date).days

        return details