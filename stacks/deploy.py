import aws_cdk as cdk
from constructs import Construct
from .asm_stack import ASMStack

class PipelineStage(cdk.Stage):
	def __init__(self, scope: Construct, id: str, **kwargs):
		super().__init__(scope, id, **kwargs)

		stack = ASMStack(self, 'ASMStack')

