from __future__ import print_function, unicode_literals
from PyInquirer import prompt, Separator
from examples import custom_style_2
import boto3
import botocore
import click
from tqdm import tqdm
import time
import json
import pandas as pd

def start_session(AWSProfile):
    try:
        boto3.setup_default_session(profile_name=AWSProfile)
        client = boto3.client('resource-explorer-2')
        return client
    except botocore.exceptions.ClientError as e:
        if e in "botocore.exceptions.EndpointConnectionError":
            print("Please check your profile configuration is correct.")
            print("Common Mistake:")
            print("- CLI default client Region")
            print("- CLI default output format")
            print("- CLI profile name")
        else:
            raise

def close_session():
    pass

@click.group()
def main():
    pass

@main.command()
def init():
    questions = [{'type': 'list', 'name': 'AWSProfile', 'message': 'Which AWS profile do you want to use?: ', 'choices': [str(profile) for profile in boto3.session.Session().available_profiles]}]
    AWSProfile = prompt(questions)['AWSProfile']
    try:
        client = start_session(AWSProfile)
    except botocore.exceptions.ClientError as e:
        if e in "botocore.exceptions.TokenRetrievalError":
            print("Please check/reconfigure AWS CLI credentails.")
            print("    - " + AWSProfile)
        else:
            raise
    response = list_view(AWSProfile)
    if response['Views'] == []:
        print("\nNo view presents.\n")
        try:
            questions = [{'type': 'confirm', 'name': 'createViews?', 'message': 'Do you want to create new views?: ', 'default': False}]
            answers = prompt(questions)
            if answers['createViews?'] == False:
                exit()
            else:
                view_arn = create_view(AWSProfile)
        except botocore.exceptions.ClientError as e:
            raise
    else:
        print("\nView(s) already exist.")
        # for view in [str(view) for view in response['Views']]:
        #     print("-", view)
        try:
            questions = [{'type': 'list', 'name': 'selectViews', 'message': 'Select which view you want to use to query: ', 'choices': [str(view) for view in response['Views']]}]
            answers = prompt(questions)
            view_arn = answers['selectViews']
        except botocore.exceptions.ClientError as e:
            raise
    questions = [{'type': 'confirm', 'name': 'saveCSV?', 'message': 'Do you want to create CSV file for output?: ', 'default': False}]
    answers = prompt(questions)
    save_lock(view_arn, AWSProfile, answers['saveCSV?'])
    print("\nPlease use following command to query:")
    print("    python main.py query\n")
            
def list_view(AWSProfile):
    print("Starting session: ")
    client = start_session(AWSProfile)
    # start_time = time.time()
    try:
        return client.list_views()
    except botocore.exceptions.ClientError as e:
        raise
    
def create_view(AWSProfile):
    client = start_session(AWSProfile)
    return client.create_view(ViewName="all-resources")['View']['ViewArn']

def save_lock(view_arn, AWSProfile, csv):
    dictionary = {"create_date": time.time(), "AWSProfile": AWSProfile, "view_arn": view_arn}
    if csv == True:
        dictionary['saveCSV'] = True
    else:
        dictionary['saveCSV'] = False
    json_object = json.dumps(dictionary, indent=4)
    with open("setup.json", "w") as outfile:
        outfile.write(json_object)

@main.command()
def query():
    try:
        with open('setup.json') as f:
            jd = json.load(f)
    except FileNotFoundError:
        print("No setup file found.\nPlease run following command to start:\n    python main.py query\n")
        raise
    AWSProfile = jd['AWSProfile']
    client = start_session(AWSProfile)
    try:
        # print(new_dataframe.head())
        choices = [
            Separator("===== Either choose ALL or manually select services ======"),
            {
                'name': 'ALL'
            },
            Separator("===== List of all services available ======"),
        ]
        # with open('services.json') as f:
        #     jd = json.load(f)
        # service_df = pd.json_normalize(jd, record_path=['Services'])
        session = boto3.Session(profile_name=AWSProfile)
        services = session.get_available_services()
        # for service in service_df.ServiceCode:
        for service in services:
            choices += [{'name': service}]
        questions = [{'type': 'checkbox', 'name': 'resourcesQuery?', 'message': 'Which resources do you want to query?: ', 'choices': choices, 'validate': lambda answer: 'You must choose at least one resource.' if len(answer) == 0 else True, 'paginate': True, 'pageSize': 100}]
        answers = prompt(questions)
        with open('setup.json', 'r') as openfile:
            view_arn = json.load(openfile)
        # print(answers['resourcesQuery?'])
        if "ALL" in answers['resourcesQuery?']:
            # print(choices)
            # resource_query(service_df.ServiceCode, view_arn)
            resource_query(services, view_arn, AWSProfile)
        else:
            # resource_query(answers['resourcesQuery?'], view_arn)
            pass
    except botocore.exceptions.ClientError as e:
        raise
    exit()
    
def resource_query(resource_list, view_arn, AWSProfile):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    client = start_session(AWSProfile)
    tmp = pd.DataFrame(columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
    for resource in resource_list:
        response = client.search(QueryString=resource, ViewArn=view_arn['view_arn'])
        try:
            if response['Resources'] == []:
                pass
            else:
                items = pd.DataFrame(response['Resources'], columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
                # resource = pd.DataFrame(columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
                # print("================================")
                # print(items.dtypes)
                # print(resource.dtypes)
                # print("================================")
                # resource = resource.append(resource, ignore_index = True)
                tmp = pd.concat([tmp, items], ignore_index=True)
                # print(resource)
                # resource = pd.DataFrame(response['Resources'], columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
                # tmp = pd.concat([resource if not resource.empty else None, tmp], verify_integrity=True, ignore_index = True)
        except ValueError as e:
            print('Could not find resource.')
        # tmp = tmp.drop_duplicates(subset=['Arn'], keep='last')
        print(resource + ": Completed")
        print("\n")
    tmp = tmp.drop_duplicates(subset=['Arn'], keep='last')
    save_to_csv(timestamp, tmp)
                
def save_to_csv(timestamp, df):
    df.to_csv(timestamp + '.csv', mode='a', index=False, header=True)

def exit():
    f = open('bye.txt', 'r')
    file_contents = f.read()
    print("\n" + file_contents + "\n")
    f.close()

if __name__ == "__main__":
    main()