from aws_cdk import (
	core,
	aws_codecommit as codecommit,
	aws_codepipeline as codepipeline, 
	aws_codepipeline_actions as codepipeline_actions,
	pipelines as pipelines
)
from aws_cdk.aws_ec2 import Action
from .deploy import PipelineStage

class ASMPipelineStack(core.Stack):

	def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
		super().__init__(scope, construct_id, **kwargs)

		# Create a codecommit repository called 'AttackSurfaceManagement'
		repo = codecommit.Repository(
			self, 'AttackSurfaceManagement',
			repository_name='AttackSurfaceManagement'
		)

		source_artifact = codepipeline.Artifact()

		cloud_assembly_artifact = codepipeline.Artifact()

		pipeline = pipelines.CdkPipeline(
			self, 'Pipeline',
			cloud_assembly_artifact=cloud_assembly_artifact,
			source_action=codepipeline_actions.CodeCommitSourceAction(
				action_name='CodeCommit',
				output=source_artifact,
				repository=repo
			),
			synth_action=pipelines.SimpleSynthAction(
				install_commands=[
					'npm install -g aws-cdk',
					'pip3 install -r requirements.txt'
				],
				environment={
					'privileged': True
				},				
				synth_command='cdk synth',
				source_artifact=source_artifact,
				cloud_assembly_artifact=cloud_assembly_artifact,
			)
		)

		deploy_stage = pipeline.add_application_stage(PipelineStage(
			self, 'LambdaDeployment'))