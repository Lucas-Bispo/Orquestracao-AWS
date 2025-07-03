# src/extractors/ec2_extractor.py

from .base_extractor import BaseExtractor

class EC2Extractor(BaseExtractor):
    """
    Extrai informações detalhadas dos recursos do EC2 e serviços relacionados.
    Esta versão foi expandida para incluir um grande número de atributos por instância.
    """
    def extract(self, aws_session):
        ec2_client = aws_session.client('ec2')
        elbv2_client = aws_session.client('elbv2')
        autoscaling_client = aws_session.client('autoscaling')
        
        print("Iniciando extração de dados do EC2 e serviços relacionados (versão detalhada)...")

        try:
            # Coleta dados auxiliares primeiro para correlacionar depois
            instance_statuses = self._get_instance_statuses(ec2_client)
            elastic_ips = self._get_elastic_ips(ec2_client)

            ec2_data = {
                'EC2_Instances_Detailed': self._get_instances(ec2_client, instance_statuses, elastic_ips),
                'EBS_Volumes': self._get_volumes(ec2_client),
                'Elastic_IPs': elastic_ips, # A aba de EIPs continua útil
                'AMIs': self._get_images(ec2_client),
                'LoadBalancers': self._get_load_balancers(elbv2_client),
                'AutoScalingGroups': self._get_auto_scaling_groups(autoscaling_client),
            }
            print("Extração de dados do EC2 concluída.")
            return ec2_data
        except Exception as e:
            print(f"\nERRO ao extrair dados do EC2: {e}")
            return {}

    def _get_instance_statuses(self, client):
        print("  - Coletando Status Checks das instâncias...")
        statuses = {}
        paginator = client.get_paginator('describe_instance_status')
        for page in paginator.paginate(IncludeAllInstances=True):
            for status in page['InstanceStatuses']:
                statuses[status['InstanceId']] = {
                    "SystemStatus": status['SystemStatus']['Status'],
                    "InstanceStatus": status['InstanceStatus']['Status']
                }
        return statuses

    def _get_instances(self, client, instance_statuses, elastic_ips):
        print("  - Coletando informações detalhadas de Instâncias EC2...")
        paginator = client.get_paginator('describe_instances')
        instances_detailed = []
        
        # Cria um mapa de InstanceId para Elastic IP para consulta rápida
        eip_map = {eip['AssociatedInstanceId']: eip['PublicIp'] for eip in elastic_ips if eip.get('AssociatedInstanceId')}

        for page in paginator.paginate(Filters=[{'Name': 'instance-state-name', 'Values': ['pending', 'running', 'shutting-down', 'stopping', 'stopped']}]):
            for reservation in page['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    status_check = instance_statuses.get(instance_id, {})
                    iam_profile = instance.get('IamInstanceProfile', {})
                    placement = instance.get('Placement', {})
                    metadata_options = instance.get('MetadataOptions', {})
                    hibernation_options = instance.get('HibernationOptions', {})

                    # Concatena os IDs de security groups e volumes
                    sg_ids = ', '.join([sg['GroupId'] for sg in instance.get('SecurityGroups', [])])
                    sg_names = ', '.join([sg['GroupName'] for sg in instance.get('SecurityGroups', [])])
                    volume_ids = ', '.join([vol['Ebs']['VolumeId'] for vol in instance.get('BlockDeviceMappings', []) if 'Ebs' in vol])

                    details = {
                        'InstanceId': instance_id,
                        'Name': next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), 'N/A'),
                        'InstanceState': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'StatusCheck': f"System: {status_check.get('SystemStatus', 'N/A')}, Instance: {status_check.get('InstanceStatus', 'N/A')}",
                        'AvailabilityZone': placement.get('AvailabilityZone', 'N/A'),
                        'PublicIPv4DNS': instance.get('PublicDnsName', 'N/A'),
                        'PublicIPv4Address': instance.get('PublicIpAddress', 'N/A'),
                        'ElasticIP': eip_map.get(instance_id, 'N/A'),
                        'IPv6Addresses': ', '.join(instance.get('Ipv6Addresses', [])),
                        'Monitoring': instance.get('Monitoring', {}).get('State', 'N/A'),
                        'SecurityGroupName': sg_names,
                        'KeyName': instance.get('KeyName', 'N/A'),
                        'LaunchTime': instance['LaunchTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'PlatformDetails': instance.get('PlatformDetails', 'N/A'),
                        'PrivateDNSName': instance.get('PrivateDnsName', 'N/A'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress', 'N/A'),
                        'SecurityGroupIDs': sg_ids,
                        'OwnerID': reservation.get('OwnerId', 'N/A'),
                        'AttachedVolumeIDs': volume_ids,
                        'RootDeviceName': instance.get('RootDeviceName', 'N/A'),
                        'RootDeviceType': instance.get('RootDeviceType', 'N/A'),
                        'EBSOptimized': instance.get('EbsOptimized', False),
                        'ImageID': instance.get('ImageId', 'N/A'),
                        'KernelID': instance.get('KernelId', 'N/A'),
                        'RamDiskID': instance.get('RamdiskId', 'N/A'),
                        'AMILaunchIndex': instance.get('AmiLaunchIndex', 'N/A'),
                        'ReservationID': reservation.get('ReservationId', 'N/A'),
                        'VPCID': instance.get('VpcId', 'N/A'),
                        'SubnetID': instance.get('SubnetId', 'N/A'),
                        'InstanceLifecycle': instance.get('InstanceLifecycle', 'On-Demand'),
                        'Architecture': instance.get('Architecture', 'N/A'),
                        'VirtualizationType': instance.get('VirtualizationType', 'N/A'),
                        'IAMInstanceProfileARN': iam_profile.get('Arn', 'N/A'),
                        'Tenancy': placement.get('Tenancy', 'N/A'),
                        'PlacementGroup': placement.get('GroupName', 'N/A'),
                        'StateTransitionReason': instance.get('StateTransitionReason', 'N/A'),
                        'StopHibernationBehavior': 'Enabled' if hibernation_options.get('Configured') else 'Disabled',
                        'IMDSv2': metadata_options.get('HttpTokens', 'N/A'),
                        'UsageOperation': instance.get('UsageOperation', 'N/A'),
                    }
                    instances_detailed.append(details)
        return instances_detailed

    # As funções abaixo (_get_volumes, _get_elastic_ips, etc.) continuam as mesmas da versão anterior.
    # Elas ainda são úteis para criar suas próprias abas dedicadas no relatório.
    def _get_volumes(self, client):
        print("  - Coletando informações de Volumes EBS...")
        # ... (código inalterado)
        volumes = client.describe_volumes()['Volumes']
        result = []
        for volume in volumes:
            name_tag = next((tag['Value'] for tag in volume.get('Tags', []) if tag['Key'] == 'Name'), 'N/A')
            attachment = volume['Attachments'][0] if volume['Attachments'] else {}
            result.append({
                'Name': name_tag,
                'VolumeId': volume['VolumeId'],
                'Size (GiB)': volume['Size'],
                'VolumeType': volume['VolumeType'],
                'State': volume['State'],
                'IOPS': volume.get('Iops', 'N/A'),
                'AttachedInstanceId': attachment.get('InstanceId', 'Detached'),
                'AvailabilityZone': volume['AvailabilityZone'],
                'CreateTime': volume['CreateTime'].strftime('%Y-%m-%d %H:%M:%S'),
            })
        return result

    def _get_elastic_ips(self, client):
        print("  - Coletando informações de Elastic IPs...")
        # ... (código inalterado)
        addresses = client.describe_addresses()['Addresses']
        result = []
        for addr in addresses:
            result.append({
                'PublicIp': addr['PublicIp'],
                'AllocationId': addr['AllocationId'],
                'Domain': addr['Domain'],
                'AssociatedInstanceId': addr.get('InstanceId', 'N/A'),
                'NetworkInterfaceId': addr.get('NetworkInterfaceId', 'N/A'),
            })
        return result

    def _get_images(self, client):
        print("  - Coletando informações de Imagens (AMIs)...")
        # ... (código inalterado)
        images = client.describe_images(Owners=['self'])['Images']
        result = []
        for image in images:
            result.append({
                'Name': image.get('Name', 'N/A'),
                'ImageId': image['ImageId'],
                'CreationDate': image['CreationDate'],
                'State': image['State'],
                'Public': image['Public'],
            })
        return result

    def _get_load_balancers(self, client):
        print("  - Coletando informações de Load Balancers (ALB/NLB)...")
        # ... (código inalterado)
        lbs = client.describe_load_balancers()['LoadBalancers']
        result = []
        for lb in lbs:
            result.append({
                'Name': lb['LoadBalancerName'],
                'ARN': lb['LoadBalancerArn'],
                'DNSName': lb['DNSName'],
                'Type': lb['Type'],
                'Scheme': lb['Scheme'],
                'VpcId': lb['VpcId'],
                'State': lb['State']['Code'],
            })
        return result

    def _get_auto_scaling_groups(self, client):
        print("  - Coletando informações de Auto Scaling Groups...")
        # ... (código inalterado)
        asgs = client.describe_auto_scaling_groups()['AutoScalingGroups']
        result = []
        for asg in asgs:
            result.append({
                'Name': asg['AutoScalingGroupName'],
                'MinSize': asg['MinSize'],
                'MaxSize': asg['MaxSize'],
                'DesiredCapacity': asg['DesiredCapacity'],
                'InstanceCount': len(asg['Instances']),
                'LaunchTemplate': asg.get('LaunchTemplate', {}).get('LaunchTemplateName', 'N/A'),
                'AvailabilityZones': ', '.join(asg['AvailabilityZones']),
            })
        return result