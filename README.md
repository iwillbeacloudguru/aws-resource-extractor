# AWS Resource Explorer Extraction App

## Introduction

This Python application is designed to extract resource information from AWS Resource Explorer. It allows you to query and retrieve data about AWS resources, making it a valuable tool for managing and analyzing your AWS environment.

## Prerequisites

Before using this application, ensure that you have the following prerequisites installed:

- Python 3.x
    https://realpython.com/installing-python/
- AWS CLI 2.x
    https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- VirtualEnvironment
    https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/
- Git
    https://git-scm.com/book/en/v2/Getting-Started-Installing-Git
- AWS Credential must have access to Organization Read-only
  <br />
## Getting Started
1. Clone this git repo to your local machine.
    ``` bash
    git clone https://github.com/iwillbeacloudguru/aws-resource-extractor.git
    ```
    <br />
2. Change directory to project folder.
    ``` bash
    cd aws-resource-extractor
    ```
    <br />
3. Create and activate virtual environment.
    ``` Python
    virtualenv -p python3.9 .env
    ```
    ``` Bash
    source .env/bin/activate
    ```
    <br />
4. Install required packages in virtual environment.
    ``` Python
    pip3 install -r requirements.txt
    ```
    <br />
5. Configure AWS CLI
    https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html
    <br />
6. Set up the AWS CLI
    https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html
    <br />
    <i>Note: Please note your AWS profile in cli that you want to use.</i>
    <br />
7. Turn on Resource Explorer. <b>Repeat this step in every account.</b></br >
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.42.23@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.43.55@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.47.50@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.50.05@2x.png>)
    <br />
8. Create IAM Role for script to assume. <b>Repeat this step in every account.</b></br >
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.51.49@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.52.57@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.53.48@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 19.57.43@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 20.03.07@2x.png>)
    ![Alt text](<assets/CleanShot 2567-01-11 at 20.04.35@2x.png>)
    <br />


## Usage

### Initialization
To start using the application, run the following command:

``` bash
python3 main.py init
```
Follow the prompts to select an AWS profile and set up your configuration.
<br />
### Querying Resources
To query AWS resources, run the following command:
``` bash
python3 main.py query
```
<br />
## Demo
![Alt text](<assets/CleanShot 2567-01-08 at 12.02.08.gif>)
<br />
## Saving Results
You can choose to save the results as a CSV file during the query process. The CSV files will be named with a timestamp.
![Alt text](<assets/CleanShot 2567-01-08 at 12.26.02@2x.png>)
<br />
## Configuration
You can modify the configuration in the setup.json file to customize your settings.
License
Porames J.
<!-- This application is open-source and available under the MIT License. -->
<br />
### Disclaimer
This application is provided as-is without any warranties. Use it at your own risk, and always follow AWS best practices and security guidelines.
<br />
### Acknowledgments

Special thanks to the libraries and tools used in this application, including PyInquirer, boto3, botocore, click, tqdm, and pandas.
<br />
### Contact

For any questions or feedback, please contact PJ at porames.jari@gmail.com.
