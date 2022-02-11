from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_ec2 as ec2, aws_ecs as ecs,
        aws_ecs_patterns as ecs_patterns,
        aws_applicationautoscaling as appscaling,
        aws_iam as iam,
        aws_ssm as ssm
)
from constructs import Construct

class Log4ShellStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc = ec2.Vpc(self, "MainVpc",
                            subnet_configuration=[
                                   ec2.SubnetConfiguration(
                                   name="public-subnet",
                                   subnet_type=ec2.SubnetType.PUBLIC
                                   )],
                            max_azs=1
                      )
        cluster = ecs.Cluster(self, "MyCluster", vpc=vpc)
        scheduled_fargate_task = ecs_patterns.ScheduledFargateTask(self, "ScheduledFargateTask",
                    cluster=cluster,
                     subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                        scheduled_fargate_task_image_options=ecs_patterns.ScheduledFargateTaskImageOptions(
                                    image=ecs.ContainerImage.from_asset("./log4shell/log4j-scanner"),
                                            memory_limit_mib=512
                                                ),
                            schedule=appscaling.Schedule.expression("rate(5 minutes)"),
                                platform_version=ecs.FargatePlatformVersion.LATEST
                                )
        with open('./log4shell/dnsserver/cloudwatch_conf.json') as f:
            cloudwatch_conf = f.read()
        ssm.StringParameter(self, 'cloudformation-template', string_value=cloudwatch_conf, parameter_name="AmazonCloudWatch-log4shell-stack-dns-conf")

        instance_type = ec2.InstanceType('t2.nano')
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
                # These settings and more can be configured for the new AL2 instance
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
                edition=ec2.AmazonLinuxEdition.STANDARD,
                virtualization=ec2.AmazonLinuxVirt.HVM,
                storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
                )
        dns_role = iam.Role(self, "Ec2DnsServerRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        dns_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchAgentServerPolicy"))
        dns_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        dns_sg = ec2.SecurityGroup(self, 'dns_sg', vpc = vpc)
        dns_sg.connections.allow_from_any_ipv4(ec2.Port.udp(53))
        
        handle = ec2.InitServiceRestartHandle()
        al2_instance = ec2.Instance(self, "AL2-Instance",
                        instance_type=instance_type,
                        machine_image=amzn_linux,
                        vpc = vpc,
                        role = dns_role,
                        security_group = dns_sg,
                        # init=ec2.CloudFormationInit.from_elements(
                        #     ec2.InitFile.from_asset('/opt/dnsserver/ddnsserver.py', './log4shell/dnsserver/ddnsserver.py', service_restart_handles = [handle]),
                        #     ec2.InitFile.from_asset('/etc/systemd/system/ddnsserver.service', './log4shell/dnsserver/ddnsserver.service', service_restart_handles = [handle]),
                        #     ec2.InitPackage.yum("amazon-cloudwatch-agent"),
                        #     ec2.InitCommand.shell_command('amazon-cloudwatch-agent-ctl -a start && amazon-cloudwatch-agent-ctl -a fetch-config -s -m ec2 -c ssm:AmazonCloudWatch-log4shell-stack-dns-conf'),
                        #     ec2.InitCommand.shell_command('pip install requests termcolor PyCryptodome dnslib', service_restart_handles = [handle]),
                        # #     ec2.InitService.enable('ddnsserver', service_restart_handle = handle)
                        #     )
                        )