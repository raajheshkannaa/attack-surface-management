import boto3
from collections import OrderedDict
from config import ORG_ACCOUNT
client = boto3.client('lambda')

def get_org_accounts(session):
	org_client = session.client('organizations')

	results = []
	messages = []
	paginator = org_client.get_paginator('list_accounts')
	response_iterator = paginator.paginate()

	for response in response_iterator:
		results = results + response['Accounts']

	for index in results:
		messages = messages + (index['Id']).split()

	return messages


def assume_role(session, aws_account_number, role_name):
	resp = session.client('sts').assume_role(
			RoleArn='arn:aws:iam::{}:role/security/{}'.format(aws_account_number,role_name),
			RoleSessionName='GatherAccounts')

	# Storing STS credentials
	creds = boto3.Session(
		aws_access_key_id = resp['Credentials']['AccessKeyId'],
		aws_secret_access_key = resp['Credentials']['SecretAccessKey'],
		aws_session_token = resp['Credentials']['SessionToken']
	)

	print("Assumed session for {}.".format(
		aws_account_number
	))

	return creds


def main(event, context):
	
	org_session = assume_role(boto3.Session(), ORG_ACCOUNT, 'org-read-001')

	accounts = get_org_accounts(org_session)

	for account in accounts:
		print(account)
		response = client.invoke(
		FunctionName='asm-2',
		InvocationType='Event',
		LogType='Tail',
		Payload='{"accountID" :"' + account + '"}'
		)

	print(response)
