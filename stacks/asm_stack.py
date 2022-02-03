from aws_cdk import (
	aws_iam as iam,
	aws_lambda as lmb,
	aws_events as events,
	aws_events_targets as targets,
	aws_ec2 as ec2,
	Duration
)

import aws_cdk as cdk
from constructs import Construct
from os import getcwd
from ..config import AUTOMATION_ACCOUNT

class ASMStack(cdk.Stack):

	def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		# Depends on the `Hub` IAM ROLE present in the Security or Automation Account.
		src_role_arn = 'arn:aws:iam::' + AUTOMATION_ACCOUNT + ':role/security/hub-001'

		src_role = iam.Role.from_role_arn(self, 'Role', src_role_arn)

				# Subnet configurations for a public and private tier
		subnet1 = ec2.SubnetConfiguration(
				name="Public",
				subnet_type=ec2.SubnetType.PUBLIC,
				cidr_mask=24)
		subnet2 = ec2.SubnetConfiguration(
				name="Private",
				subnet_type=ec2.SubnetType.PRIVATE,
				cidr_mask=24)

		vpc = ec2.Vpc(self,
				  "ASMVPC",
				  cidr="10.187.0.0/16", # Please change this if this would cause a conflict.
				  enable_dns_hostnames=True,
				  enable_dns_support=True,
				  max_azs=2,
				  nat_gateway_provider=ec2.NatProvider.gateway(),
				  nat_gateways=1,
				  subnet_configuration=[subnet1, subnet2]
				  )


		asm1 = lmb.Function(
			self, 'asm-1',
			code=lmb.Code.asset('src/asm-1'),
			runtime=lmb.Runtime.PYTHON_3_9,
			handler='asm-1.main',
			timeout=Duration.seconds(900),
			memory_size=128,
			role=src_role,
			function_name='asm-1',
			vpc=vpc,
			vpc_subnets=ec2.SubnetType.PRIVATE,
		)

		asm2 = lmb.Function(
			self, 'asm-2',
			code=lmb.Code.asset('src/asm-2'),
			runtime=lmb.Runtime.PYTHON_3_9,
			handler='asm-2.main',
			timeout=Duration.seconds(900),
			memory_size=128,
			role=src_role,
			function_name='asm-2',
			vpc=vpc,
			vpc_subnets=ec2.SubnetType.PRIVATE,
		)

		# Absolute path of Dockerfile, cos this is needed for local developement and testing of the container image
		dockerfile=getcwd() + '/src/asm-3'
		asm3 = lmb.DockerImageFunction(
			self, 'asm-3',
			code=lmb.DockerImageCode.from_image_asset(dockerfile),
			timeout=Duration.seconds(900),
			memory_size=128,
			role=src_role,
			function_name='asm-3',
			vpc=vpc,
			vpc_subnets=ec2.SubnetType.PRIVATE

		)

		rule = events.Rule(
			self, "TriggerAttackSurfaceManagement",
			schedule=events.Schedule.cron(
				minute='0',
				hour='0',
				month='*',
				week_day='*',
				year='*'
			)
		)
		rule.add_target(targets.LambdaFunction(asm1))