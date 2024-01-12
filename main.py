from __future__ import print_function, unicode_literals
from PyInquirer import prompt, Separator
import boto3
import botocore
import click
from datetime import datetime
import json
import pandas as pd
import warnings
import logging
warnings.simplefilter(action='ignore', category=FutureWarning)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
import concurrent.futures

def start_session(AWSProfile, account):
    try:
        boto3.setup_default_session(profile_name=AWSProfile)
        sts_client = boto3.client('sts')
        response = sts_client.assume_role(
            RoleArn="arn:aws:iam::" + account +":role/ResourceExplorerRole",
            RoleSessionName="AssumeRoleSession1"
        )
        new_session = boto3.Session(aws_access_key_id=response['Credentials']['AccessKeyId'],
                            aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                            aws_session_token=response['Credentials']['SessionToken'],
                            region_name="ap-southeast-1")
        return new_session
    except botocore.exceptions.ClientError as e:
        if e in "botocore.exceptions.EndpointConnectionError":
            logging.error("Please check your profile configuration is correct.")
            logging.info("Common Mistake:")
            logging.info("- CLI default client Region")
            logging.info("- CLI default output format")
            logging.info("- CLI profile name")
        else:
            raise

def list_org_accounts(AWSProfile):
    boto3.setup_default_session(profile_name=AWSProfile)
    org_client = boto3.client('organizations')
    accounts_response = org_client.list_accounts()
    accounts = []
    account_choices = [
            Separator("===== Either choose ALL or manually select accounts ======"),
            {
                'name': 'ALL'
            },
            Separator("===== List of all accounts available ======"),
        ]
    for account in accounts_response['Accounts']:
        accounts += [account['Id']]
        account_choices += [{'name': account['Id']}]
    return {"account_choices": account_choices, "accounts": accounts}

def create_view(account):
    client = start_session("", account)
    try:
        return client.create_view(ViewName="all-resources")['View']['ViewArn']
    except botocore.exceptions.ClientError as e:
        raise

@click.group()
def main():
    logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

@main.command()
def init():
    view_arn = []
    questions = [{'type': 'list', 'name': 'AWSProfile', 'message': 'Which AWS profile do you want to use?: ', 'choices': [str(profile) for profile in boto3.session.Session().available_profiles]}]
    AWSProfile = prompt(questions)['AWSProfile']
    try:
        tmp = list_org_accounts(AWSProfile)
        account_choices, accounts = tmp['account_choices'], tmp['accounts']
        org_questions = [{'type': 'checkbox', 'name': 'organization', 'message': 'Select which account in organization to query: ', 'choices': account_choices,'validate': lambda answer: 'You must choose at least one resource.' if len(answer) == 0 else True, 'paginate': True, 'pageSize': 100}]
        for account in accounts:
            re2_client = start_session(AWSProfile, account).client('resource-explorer-2')
            response = re2_client.list_views()
            if response['Views'] == []:
                logging.info("No view presents.")
                try:
                    questions = [{'type': 'confirm', 'name': 'createViews?', 'message': 'Do you want to create new views?: ', 'default': False}]
                    answers = prompt(questions)
                    if answers['createViews?'] == False:
                        exit()
                    else:
                        view_arn += [create_view(AWSProfile)]
                except botocore.exceptions.ClientError as e:
                    raise
            else:
                logging.info("View(s) already exist in account " + account + ".")
                try:
                    questions = [{'type': 'list', 'name': 'selectViews', 'message': 'Select which view you want to use to query: ', 'choices': [str(view) for view in response['Views']]}]
                    answers = prompt(questions)
                    view_arn += [answers['selectViews']]
                except botocore.exceptions.ClientError as e:
                    if e in "botocore.exceptions.ClientError: An error occurred (AccessDenied) when calling the AssumeRole operation:":
                        logging.info("Please check that IAM role trusted relationship and role name are valid.")
                    else:
                        raise
    except botocore.exceptions.ClientError as e:
        if e in "botocore.exceptions.TokenRetrievalError":
            logging.info("Please check/reconfigure AWS CLI credentails.")
            logging.info("    - " + AWSProfile)
        else:
            raise
    logging.info("")
    questions = [{'type': 'confirm', 'name': 'saveCSV?', 'message': 'Do you want to create CSV file for output?: ', 'default': False}]
    csv_answers = prompt(questions)
    logging.info("")
    org_answers = prompt(org_questions)
    if 'ALL' in org_answers['organization']:
        save_lock(view_arn, AWSProfile, accounts, csv_answers['saveCSV?'])
    else:
        save_lock(view_arn, AWSProfile, org_answers['organization'], csv_answers['saveCSV?'])
    logging.info("Please use following command to query:")
    logging.info("    python main.py query")

def save_lock(view_arn, AWSProfile, accounts, csv):
    dictionary = {"create_date": str(datetime.now()), "AWSProfile": AWSProfile, "view_arn": view_arn, "accounts": accounts}
    if csv == True:
        dictionary['saveCSV'] = True
    else:
        dictionary['saveCSV'] = False
    json_object = json.dumps(dictionary, indent=4)
    with open("setup.json", "w") as outfile:
        outfile.write(json_object)

@main.command()
def query():
    total = pd.DataFrame(columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
    try:
        with open('setup.json') as f:
            jd = json.load(f)
    except FileNotFoundError:
        logging.info("No setup file found.Please run following command to start:    python main.py query")
        raise
    AWSProfile = jd['AWSProfile']
    # client = start_session(AWSProfile)
    try:
        choices = [
            Separator("===== Either choose ALL or manually select services ======"),
            {
                'name': 'ALL'
            },
            Separator("===== List of all services available ======"),
        ]
        session = boto3.Session(profile_name=AWSProfile)
        services = session.get_available_services()
        for service in services:
            choices += [{'name': service}]
        questions = [{'type': 'checkbox', 'name': 'resourcesQuery?', 'message': 'Which resources do you want to query?: ', 'choices': choices, 'validate': lambda answer: 'You must choose at least one resource.' if len(answer) == 0 else True, 'paginate': True, 'pageSize': 100}]
        answers = prompt(questions)
        with open('setup.json', 'r') as openfile:
            view_arn = json.load(openfile)
        if "ALL" in answers['resourcesQuery?']:
            t1_start = perf_counter()
            logging.info("Max worker of 1 is recommended due to AWS API Throttelling.")
            questions = [{'type': 'list', 'name': 'worker', 'message': 'Select max worker in process: ', 'choices': ["1", "2", "3", "4", "5"]}]
            worker = int(prompt(questions)['worker'])
            for account in jd['accounts']:
                print("Start account " + account + " query.")
                tmp = resource_query(services, view_arn, AWSProfile, account, worker)
                total = pd.concat([total, tmp], ignore_index=True, verify_integrity=True, axis=0)
                print("====================================")
            t1_stop = perf_counter()
            print("Elapsed time during the query in seconds:", int(t1_stop-t1_start), "s")
            total = total.drop_duplicates(subset=['Arn'], keep='last')
            t1_stop = perf_counter()
            print("Elapsed time during the query in seconds:", int(t1_stop-t1_start))
            save_to_csv(datetime.now(), total)
        else:
            exit()
    except botocore.exceptions.ClientError as e:
        raise
    exit()
    
def resource_query(resource_list, view_arn, AWSProfile, account, worker):
    tmp = pd.DataFrame(columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
    view = ""
    for arn in view_arn['view_arn']:
        if arn.startswith("arn:aws:resource-explorer-2:ap-southeast-1:" + str(account) + ":view/all-resources/"):
            view = arn
        else:
            pass
    # rl_1, rl_2 = resource_list[::2], resource_list[1::2]
    re2_client = start_session(AWSProfile, account).client('resource-explorer-2')
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker) as executor:
        results = [executor.submit(task_wrapper, args=(resource, view, AWSProfile, account, re2_client)) for resource in resource_list]
        for future in concurrent.futures.as_completed(results):
            result = future.result()
            # logging.info(result)
            try:
                if result['Resources'] == []:
                    # logging.warning('Could not find the resource.')
                    pass
                else:
                    items = pd.DataFrame(result['Resources'], columns = ['Arn', 'LastReportedAt', 'OwningAccountId', 'Properties', 'Region', 'ResourceType', 'Service'])
                    tmp = pd.concat([tmp, items], ignore_index=True, verify_integrity=True, axis=0)
            except ValueError as e:
                logging.warning('Could not find resource.')
    return tmp

def task(resource, view, AWSProfile, account, re2_client):
    # re2_client = start_session(AWSProfile, account).client('resource-explorer-2')
    print(resource + " => COMPLETED")
    return re2_client.search(QueryString=resource, ViewArn=view)

def task_wrapper(args):
    return task(*args)

def save_to_csv(timestamp, df):
    df.to_csv(str(timestamp) + '.csv', mode='a', index=False, header=True)

def exit():
    f = open('bye.txt', 'r')
    file_contents = f.read()
    print("" + file_contents + "")
    f.close()

if __name__ == "__main__":
    main()