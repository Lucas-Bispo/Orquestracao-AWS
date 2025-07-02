from .base_extractor import BaseExtractor

class VPCExtractor(BaseExtractor):
    """
    Extrai informações detalhadas dos componentes da VPC, como
    VPCs, Subnets, Route Tables, e Security Groups.
    """
    def extract(self, aws_session):
        ec2_client = aws_session.client('ec2')
        print("Iniciando extração de dados da VPC...")

        try:
            vpc_data = {
                'VPCs': self._get_vpcs(ec2_client),
                'Subnets': self._get_subnets(ec2_client),
                'RouteTables': self._get_route_tables(ec2_client),
                'SecurityGroups': self._get_security_groups(ec2_client),
                'InternetGateways': self._get_internet_gateways(ec2_client),
                'NatGateways': self._get_nat_gateways(ec2_client),
            }
            print("Extração de dados da VPC concluída.")
            return vpc_data
        except Exception as e:
            print(f"\nERRO ao extrair dados da VPC: {e}")
            return {}

    def _get_vpcs(self, client):
        print("  - Coletando informações de VPCs...")
        vpcs = client.describe_vpcs()['Vpcs']
        result = []
        for vpc in vpcs:
            name_tag = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            result.append({
                'Name': name_tag,
                'VPCId': vpc['VpcId'],
                'CIDRBlock': vpc['CidrBlock'],
                'IsDefault': vpc['IsDefault'],
                'State': vpc['State'],
            })
        return result

    def _get_subnets(self, client):
        print("  - Coletando informações de Subnets...")
        subnets = client.describe_subnets()['Subnets']
        result = []
        for subnet in subnets:
            name_tag = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            result.append({
                'Name': name_tag,
                'SubnetId': subnet['SubnetId'],
                'VPCId': subnet['VpcId'],
                'CIDRBlock': subnet['CidrBlock'],
                'AvailabilityZone': subnet['AvailabilityZone'],
                'AvailableIpAddressCount': subnet['AvailableIpAddressCount'],
                'State': subnet['State'],
            })
        return result

    def _get_route_tables(self, client):
        print("  - Coletando informações de Route Tables...")
        tables = client.describe_route_tables()['RouteTables']
        result = []
        for table in tables:
            name_tag = next((tag['Value'] for tag in table.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            routes_formatted = []
            for route in table['Routes']:
                target = route.get('GatewayId') or route.get('NatGatewayId') or route.get('InstanceId') or 'N/A'
                routes_formatted.append(f"Dest: {route['DestinationCidrBlock']} -> Target: {target}")
            
            result.append({
                'Name': name_tag,
                'RouteTableId': table['RouteTableId'],
                'VPCId': table['VpcId'],
                'Routes': '; '.join(routes_formatted),
            })
        return result

    def _get_security_groups(self, client):
        print("  - Coletando informações de Security Groups...")
        groups = client.describe_security_groups()['SecurityGroups']
        result = []
        for group in groups:
            inbound_rules = []
            for rule in group['IpPermissions']:
                from_port = rule.get('FromPort', 'N/A')
                to_port = rule.get('ToPort', 'N/A')
                protocol = rule.get('IpProtocol', '-1')
                sources = ', '.join([rng['CidrIp'] for rng in rule.get('IpRanges', [])])
                inbound_rules.append(f"Proto: {protocol}, Port: {from_port}-{to_port}, Src: {sources}")
            
            result.append({
                'GroupName': group['GroupName'],
                'GroupId': group['GroupId'],
                'VPCId': group['VpcId'],
                'Description': group['Description'],
                'InboundRules': '; '.join(inbound_rules) if inbound_rules else 'N/A'
            })
        return result

    def _get_internet_gateways(self, client):
        print("  - Coletando informações de Internet Gateways...")
        igws = client.describe_internet_gateways()['InternetGateways']
        result = []
        for igw in igws:
            name_tag = next((tag['Value'] for tag in igw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachment = igw['Attachments'][0] if igw['Attachments'] else {}
            result.append({
                'Name': name_tag,
                'InternetGatewayId': igw['InternetGatewayId'],
                'AttachedVPCId': attachment.get('VpcId', 'Detached'),
                'State': attachment.get('State', 'N/A'),
            })
        return result
        
    def _get_nat_gateways(self, client):
        print("  - Coletando informações de NAT Gateways...")
        ngws = client.describe_nat_gateways()['NatGateways']
        result = []
        for ngw in ngws:
            name_tag = next((tag['Value'] for tag in ngw.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            ip_info = ngw['NatGatewayAddresses'][0] if ngw['NatGatewayAddresses'] else {}
            result.append({
                'Name': name_tag,
                'NatGatewayId': ngw['NatGatewayId'],
                'VPCId': ngw['VpcId'],
                'SubnetId': ngw['SubnetId'],
                'State': ngw['State'],
                'PublicIp': ip_info.get('PublicIp', 'N/A'),
                'PrivateIp': ip_info.get('PrivateIp', 'N/A'),
            })
        return result
