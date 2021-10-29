from aws_cdk import (
	core
)

from .asm_stack import ASMStack

class PipelineStage(core.Stage):
	def __init__(self, scope: core.Construct, id: str, **kwargs):
		super().__init__(scope, id, **kwargs)

		stack = ASMStack(self, 'ASMStack')

