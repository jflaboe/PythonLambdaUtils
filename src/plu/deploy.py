import json
import os
import shutil
import time
import zipfile

import boto3

def run(args):
    if len(args) < 3:
        print("Usage:\n\npython -m plu deploy <package> [...<package2>]\npython -m plu deploy all")
    packages = args[2:]
    if "all" in packages:
        deploy_all()
    else:
        for p in packages:
            deploy_package(p)

def deploy_all():
    for p in get_all_lambdas():
        deploy_package(p)

def get_all_lambdas():
    with open(".plu") as f:
        return [v for v in json.loads(f.read()).values()]

def deploy_package(package_name):
    print("Deploying Lambda for: {}".format(package_name))
    print("Copying dependencies...")
    copy_modules(package_name)
    print("Copying main modules...")
    copy_top_level_files(package_name)
    print("Zipping up contents...")
    zip_deployment_directory_contents(package_name)
    print("Deploying to AWS...")
    upload_lambda(package_name)
    print("Deployment complete. Cleaning up...")
    remove_zip_file(package_name)
    remove_deployment_directory(package_name)

def remove_deployment_directory(package_name):
    shutil.rmtree(get_deployment_directory_path(package_name))

def get_deployment_directory_path(package_name):
    return "./{}/tmp-deploy".format(package_name)

def zip_deployment_directory_contents(package_name):
    with zipfile.ZipFile(get_zip_file_path(package_name), 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipdir(get_deployment_directory_path(package_name), zipf)

def remove_zip_file(package_name):
    os.remove(get_zip_file_path(package_name))

def get_zip_file_path(package_name):
    return "./{}/tmp-deploy-zip.zip".format(package_name)

def copy_modules(package_name):
    shutil.copytree("./{}/env/Lib/site-packages".format(package_name), get_deployment_directory_path(package_name))

def copy_top_level_files(package_name):
    for filename in os.listdir("./{}".format(package_name)):
        if len(filename) > 3 and filename[-3:] == ".py":
            with open("./{}/{}".format(package_name, filename)) as f:
                data = f.read().split("\n")
                for i in range(len(data)):
                    if data[i].startswith("from ."):
                        data[i] = data[i][7:]
                with open("{}/{}".format(get_deployment_directory_path(package_name), filename), "w") as g:
                    g.write("\n".join(data))

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file), 
                       os.path.relpath(os.path.join(root, file), 
                                       path))

def upload_lambda(package_name):
    client = boto3.client("lambda", region_name=get_aws_region())
    pname = get_project_name()
    with open(get_zip_file_path(package_name), "rb") as z:
        try:
            #check if function exists
            client.get_function(FunctionName=pname + "_" + package_name)

            response = client.update_function_code(
                FunctionName=pname + "_" + package_name,
                ZipFile=z.read()
            )
        except:
            arn = input("Role ARN for this Lambda function?: ")
            client.create_function(
                FunctionName=pname + "_" + package_name,
                Runtime="python3.9",
                Handler="lambda_function.lambda_handler",
                Role=arn,
                Code={
                    "ZipFile": z.read()
                }
            )
    env = get_environment_variables()
    if not env is None:
        print("Deployment started, waiting for completion...")
        time.sleep(15)
        client.update_function_configuration(
            FunctionName=pname + "_" + package_name,
            Environment={
                "Variables": env
            }
        )
    
            
def get_environment_variables():
    if os.path.isfile(".plu.env") is True:
        with open(".plu.env") as f:
            return json.loads(f.read())

    return None

def get_aws_region():
    if os.path.isfile(".plu.conf") is True:
        with open(".plu.conf") as f:
            data = json.loads(f.read())
        if "region" in data:
            return data['region']
        else:
            region = input("AWS Region for lambda upload?: ")
            data["region"] = region
            with open(".plu.conf", "w") as f:
                f.write(json.dumps(data))

    else:
        region = input("AWS Region for lambda upload?: ")
        if region in ["us-west-2", "us-west-1", "us-east-1", "us-east-2"]:
            with open(".plu.conf", "w") as f:
                f.write(json.dumps({"region": region}))
        return region
    return "us-west-2"

def get_project_name():
    if os.path.isfile(".plu.conf") is True:
        with open(".plu.conf") as f:
            data = json.loads(f.read())
        if "project" in data:
            return data['project']
        else:
            pname = input("Project name?: ")
            data["project"] = pname
            with open(".plu.conf", "w") as f:
                f.write(json.dumps(data))

    else:
        pname = input("Project name?: ")
        with open(".plu.conf", "w") as f:
            f.write(json.dumps({"project": pname}))
        return pname
    return "us-west-2"

