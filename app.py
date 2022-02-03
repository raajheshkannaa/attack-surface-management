#!/usr/bin/env python3

from stacks.asm_stack import ASMStack
from stacks.pipeline_stack import ASMPipelineStack
import aws_cdk as cdk
from config import AUTOMATION_ACCOUNT

automation_account_env = { 'account': AUTOMATION_ACCOUNT, 'region': 'us-east-1' }

app = cdk.App()
#ASMStack(app, "ASM-Stack") # This is not needed to be deployed directly now, since this is deployed as a stage in the pipeline.
ASMPipelineStack(app, "Pipeline-Stack", env=automation_account_env)

app.synth()
