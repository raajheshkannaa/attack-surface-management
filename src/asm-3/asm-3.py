import boto3
from botocore.exceptions import ClientError
import nmap3
from urllib.request import urlopen, URLError, HTTPError
import json
import os
from botocore.vendored import requests
from datetime import date
from config import HOOK_URL
# Instantiate nmap object for port scanning
#nmap = nmap3.NmapScanTechniques()
nmap = nmap3.Nmap()


def alert_slack(target, port, account, service):
	'''
	Implement kms to hold and protect the Slack Hook url.
	'''
	#HOOK_URL = "https://" + boto3.client('kms').decrypt(CiphertextBlob=b64decode(ENCRYPTED_HOOK_URL))['Plaintext']
	
	attachments = [
		{
		"fallback": 'Nothing to see here',
		"attachment_type": "default",
		"fields": [
			{"title": "Message", "value": "Detected an open port", "short": False},
			{"title": "IPAddress", "value": target, "short": True},
			{"title": "Port", "value": port, "short": True},
			{"title": "Account", "value": account, "short": True},
			{"title": "Service", "value": service, "short": True},
				],
		#"image_url": "https://cdn2.iconfinder.com/data/icons/amazon-aws-stencils/100/Deployment__Management_copy_IAM_Add-on-512.png",
		"color": "#ad0614"
		}
	]

	print(attachments)
	slack_message = {
		'channel': '#AWSAttackSurfaceDiscovery',
		#"text": "We have a new detection!",
		'attachments': attachments,
		'username': "AWS Attack Surface Management",
		'icon_emoji': ':robot_face:'
		}
	

	try:
		response = requests.post(HOOK_URL, data=json.dumps(slack_message))
		if response.status_code == 200:
			print("Message posted to channel")
	except HTTPError as e:
		print("Request failed: " + e.code + " " + e.reason)
	except URLError as e:
		print("Server connection failed: " + e.reason)


# Function for adding IP Address, port, service and account information after nmap scan
# This will make sure we don't alert on the same finding every time a scan is run on the same IP address, if it is not resolved. 
def put_state(ipaddress, port):
	
	table_name = 'aas-detections'
	client = boto3.client('dynamodb', region_name='us-east-1')
	
	put_item_response = client.put_item(
	TableName = table_name,
	Item={
		'ipaddress': {
			'S': ipaddress,
			},
		'port': {
			'S': port,
		}
		}
	)

	#print(put_item_response)

def get_state(ipaddress, port):

	table_name = 'aas-detections'
	client = boto3.client('dynamodb', region_name='us-east-1')
	
	try:
		get_item_response = client.get_item(
		TableName = table_name,
		Key={
		'ipaddress': {
			'S': ipaddress,
			},
		'port': {
			'S': port,
		}
		}
		)

		if 'Item' in get_item_response.keys():
			item = get_item_response["Item"]
			#return(item['ipaddress']['S'],item['port']['S'])
			return('Found')
		else:
			return []
		
	except ClientError as e:
		print(e)


def main(event, context):
	target = event['target']
	account = event['account']
	service = event['service']

	# We use the Vulners scripts for Vulnerability Scanning along with port detection.
	results = nmap.nmap_version_detection(target, args="--script vuln --script-args mincvss+5.0")
	#print(results)

	accepted_ports = {'80', '443'} # Add allowed ports here to be whitelisted from detection notifications.

	for i in range(len(results[target]['ports'])):
		state = results[target]['ports'][i]['state'] 
		port = results[target]['ports'][i]['portid']
		status = get_state(target,port)
		if status == 'Found':
			# If DynamoDB already has the items, we ignore and move on
			#print('Existing entries found!')
			continue
		else:
			if state == 'open':
				if port not in accepted_ports:
					# We add the items to the table, so that it doesn't get alerted again.
					put_state(target, port)
					# Send details to Slack Channel
					alert_slack(target, port, account, service)