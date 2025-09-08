import argparse

import boto3

parser = argparse.ArgumentParser(description='Get SSM parameters by environment')
parser.add_argument('--env', type=str, default='development', choices=['development', 'testing', 'production'])

args = parser.parse_args()
environment = args.env

ssm = boto3.client('ssm')

all_params = []

response = ssm.get_parameters_by_path(Path=f'/ichrisbirch/{environment}/', Recursive=True, WithDecryption=True)
all_params.extend(response['Parameters'])
while 'NextToken' in response:
    response = ssm.get_parameters_by_path(
        Path=f'/ichrisbirch/{environment}/', Recursive=True, WithDecryption=True, NextToken=response['NextToken']
    )
    all_params.extend(response['Parameters'])

for param in all_params:
    env_var_name = '_'.join(param['Name'].split('/')[3:]).upper()
    print(f'{env_var_name}={param["Value"]}')
