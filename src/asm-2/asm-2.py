
'''
This is an ugly script. Please feel free to clear up and help build a better script by contributing to the code in github. Thank You.

Objective is to traverse all and any AWS Service accross all our AWS Accounts which is capable of having an external IP Address or an entity which
could be reached from the internet is acquired.

AWS Services Covered
* Beanstalk
* ELB, ELBv2
* EC2
* API Gateway
* RDS
* Redshift
* Elasticsearch
* Cloudfront
* Lightsail

'''
from time import sleep
from datetime import date
from botocore.vendored import requests

import socket
import boto3
import socket
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from collections import OrderedDict
from botocore.exceptions import ClientError

# checks if the provided IP or DNS does NOT have an INTERNAL IP.
def is_private(dns):
	ip_private = ['10', '172']
	ip_address = socket.gethostbyname(dns)
	for octect in ip_private:
		if str(ip_address)[:2] == octect:
			return dns
		elif str(ip_address)[:3] == octect:
			return dns


def get_beanstalk_ip_list(session):
	
	ip_list = []
	regions = session.get_available_regions('elasticbeanstalk')
	for region_name in regions:
		try:
			client = session.client('elasticbeanstalk', region_name=region_name)
			response = client.describe_environments()
			environments = response['Environments']
			for environment in environments:
				if 'EndpointURL' in environment:
					dns_name = environment['EndpointURL']
					try:
						ip = socket.gethostbyname(dns_name)
						if not is_private(ip):
							ip_list.append(ip)
					except:
						continue
						print("Could not resolve DNS!")
			sleep(1) #Prevent rate limiting
			
		except ClientError as e:
			#print(e.response['Error']['Code'])
			if e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass
			elif e.response['Error']['Code'] == 'AuthFailure':
				pass

	return ip_list


def get_ec2_ip_list(session):
	
	instance_ip_list = []
	address_ip_list = []
	regions = session.get_available_regions('ec2')
	
	for region_name in regions:
		try:
			client = session.client('ec2', region_name=region_name)
			paginator = client.get_paginator('describe_instances')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 10})
			for page in response_iterator:
				reservations = page['Reservations']
				for reservation in reservations:
					instances = reservation['Instances']
					for instance in instances:
						if 'PublicIpAddress' in instance:
							ip = instance['PublicIpAddress']
							instance_ip_list.append(ip)
	
			response = client.describe_addresses()
			addresses = response['Addresses']
			for address in addresses:
				ip = address['PublicIp']
				address_ip_list.append(ip)
	
			sleep(1) #Prevent rate limiting

		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass
		
	return instance_ip_list


def get_elb_ip_list(session):

	ip_list = []
	regions = session.get_available_regions('elb')
	for region_name in regions:
		try:
	
			client = session.client('elb', region_name=region_name)
			paginator = client.get_paginator('describe_load_balancers')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 10})
			for page in response_iterator:
				load_balancers = page['LoadBalancerDescriptions']
				for load_balancer in load_balancers:
					dns_name = load_balancer['DNSName']
					ip = socket.gethostbyname(dns_name)
					if not is_private(dns_name):
						ip_list.append(ip)
			sleep(1) #Prevent rate limiting
		
		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list


def get_elbv2_ip_list(session):

	ip_list = []
	regions = session.get_available_regions('elbv2')
	for region_name in regions:
		try:
			client = session.client('elbv2', region_name=region_name)
			paginator = client.get_paginator('describe_load_balancers')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 10})
			for page in response_iterator:
				load_balancers = page['LoadBalancers']
				for load_balancer in load_balancers:
					dns_name = load_balancer['DNSName']
					ip = socket.gethostbyname(dns_name)
					if not is_private(dns_name):
						ip_list.append(ip)
			sleep(1) #Prevent rate limiting

		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			if e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list

def get_rds_ip_list(session):

	ip_list = []
	regions = session.get_available_regions('rds')
	for region_name in regions:
		try:
			client = session.client('rds', region_name=region_name)
			paginator = client.get_paginator('describe_db_instances')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 100})
			for page in response_iterator:
				db_instances = page['DBInstances']
				for db_instance in db_instances:
					address = db_instance['Endpoint']['Address']
					dns_name = address
					ip = socket.gethostbyname(dns_name)
					if not is_private(dns_name):
						ip_list.append(ip)
	
	
			sleep(1) #Prevent rate limiting

		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list

def get_apigateway_ip_list(session):

	ip_list = []
	regions = session.get_available_regions('apigateway')

	for region_name in regions:
		try:
			client = session.client('apigateway', region_name=region_name)
			paginator = client.get_paginator('get_rest_apis')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 100})
			for page in response_iterator:
				apis = page['items']
				for api in apis:
					id = api['id']
					address = id + ".execute-api." + region_name + ".amazonaws.com"
					#print(address)
					ip = socket.gethostbyname(address)
					if not is_private(ip):
						ip_list.append(ip)

			sleep(1)
		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list

def get_cloudfront_ip_list(session):

	ip_list = []
	try:
		client = session.client('cloudfront')
		paginator = client.get_paginator('list_distributions')
		response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 100})
		for page in response_iterator:
			dlists = page['DistributionList']
			#print(dlists.keys())
			for key in dlists.keys():
				if key == 'Items':
					#print(type(dlists[key]))
					for field in dlists[key]:
						for value in field:
							if value == 'DomainName':
								dns_name = field[value]
								try:
									ip = socket.gethostbyname(dns_name)
									if not is_private(ip):
										ip_list.append(ip) 
								except:
									pass
									   
		sleep(1)
	except ClientError as e:
		if e.response['Error']['Code'] == 'AuthFailure':
			pass
		elif e.response['Error']['Code'] == 'InvalidClientTokenId':
			pass

	return ip_list


def get_redshift_ip_list(session):
	ip_list = []
	regions = session.get_available_regions('redshift')

	for region_name in regions:
		try:
			client = session.client('redshift', region_name=region_name)
			paginator = client.get_paginator('describe_clusters')
			response_iterator = paginator.paginate(PaginationConfig={'PageSize' : 100})
			for page in response_iterator:
				clusters = page['Clusters']
				for cluster in clusters:
					public = cluster['PubliclyAccessible'] # This means the cluster is publicly available
					# However we are going to process this information regardless of whether this cluster is public
					# and still send this info to Qualys for a scan. 
					# Cos this would be bring in an asset into Qualys, which means we have Redshift setup
					endpoint = cluster['Endpoint']
					nodes = cluster['ClusterNodes']
					try:
					#if public is True: # We would use this condition if we were to check for public redshift clusters 
						if endpoint:
							for key in endpoint.keys():
								if key == 'Address':
									address = endpoint[key]
									ip = socket.gethostbyname(address)
									if not is_private(ip):
										ip_list.append(ip)
						
						if nodes:
							for i in range(len(nodes)):
								for key in nodes[i].keys():
									if key == 'PublicIPAddress':
										address = nodes[i][key]
										ip = socket.gethostbyname(address)
										if not is_private(ip):
											ip_list.append(ip)
					
					except:
						pass

			sleep(1)
		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list    


def get_lightsail_ip_list(session):

	ip_list = []
	regions = session.get_available_regions('lightsail')
	for region_name in regions:
		try:
			client = session.client('lightsail', region_name=region_name)
			
			paginator1 = client.get_paginator('get_instances')
			response_iterator1 = paginator1.paginate()
			
			paginator2 = client.get_paginator('get_load_balancers')
			response_iterator2 = paginator2.paginate()
			
			for page in response_iterator1:
				instances = page['instances']
				for instance in instances:
					address = instance['publicIpAddress']
					try:
						ip = socket.gethostbyname(address)
						if not is_private(ip):
							ip_list.append(ip)
					except:
						pass
			
			for page in response_iterator2:
				load_balancers = page['loadBalancers']
				for load_balancer in load_balancers:
					dns_name = load_balancer['dnsName']
					try:
						ip = socket.gethostbyname(dns_name)
						if not is_private(ip):
							ip_list.append(ip)
					except:
						pass

			sleep(1) #Prevent rate limiting

		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			if e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list

def get_elasticsearch_ip_list(session):
	
	ip_list = []
	regions = session.get_available_regions('es')
	for region_name in regions:
		try:
			client = session.client('es', region_name=region_name)
			response = client.list_domain_names()
			domain_names = response['DomainNames']
			for i in range(len(domain_names)):
				for key in domain_names[i].keys():
					res2 = client.describe_elasticsearch_domain(DomainName = domain_names[i][key])['DomainStatus']
					if 'Endpoints' in res2:
						# This means this is an internal VPC Elasticsearch instance. 
						# No public Address per se
						for item in res2['Endpoints'].keys():
							address = res2['Endpoints'][item]
							try:
								ip = socket.gethostbyname(address)
								if not is_private(ip):
										ip_list.append(ip)
							except:
								pass
					else:
						address = res2['Endpoint']
						try:
							ip = socket.gethostbyname(address)
							if not is_private(ip):
								ip_list.append(ip)
						except:
							pass

			sleep(1) #Prevent rate limiting

		except ClientError as e:
			if e.response['Error']['Code'] == 'AuthFailure':
				pass
			elif e.response['Error']['Code'] == 'InvalidClientTokenId':
				pass

	return ip_list


# The core component of our Lambda which is used to make the role assumptions and make the multiple jumps 
# accross accounts.
def assume_role(session, aws_account_number, role_name):
	resp = session.client('sts').assume_role(
		RoleArn='arn:aws:iam::{}:role/security/{}'.format(aws_account_number,role_name),
		RoleSessionName='Attack_Surface_Discovery')

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


# main function called by the Lambda Handler
def main(event, context):

	spoke_role = 'spoke-001'
	account = event['accountID']
	account = ''.join(account)

	session = assume_role(boto3.Session(), account, spoke_role)
	
	services = {'beanstalk', 'ec2', 'elb', 'elbv2', 'rds', 'apigateway', 'cloudfront', 'redshift', 'lightsail', 'elasticsearch'}
	
	#services = {'ec2'}
	for service in services:
		
		get_function = globals()['get_' + service + '_ip_list']
		ip_list = get_function(session)

		client = boto3.client('lambda')

		for target in ip_list:
			response = client.invoke(
			FunctionName='asm-3',
			InvocationType='Event',
			LogType='Tail',
			Payload='{"target" :"' + target + '", "account" :"' + account + '", "service" :"' + service + '" }'
			)