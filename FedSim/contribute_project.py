import argparse
import glob

from featurecloud_api import User, Project, FCC



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a FeatureCloud project as coordinator")
    parser.add_argument("-u", "--user", help="Username for FeatureCloud login")
    parser.add_argument("-p", "--project", help="project ID")
    args = parser.parse_args()
    return args


def main(username, project_id) -> None:
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    fcc = FCC(user=user, project=proj)
    # upload all files in fedsim_data/
    # finalisation of upload is triggered at the end
    files_to_upload = list(glob.glob("fedsim_data/*"))
    fcc.upload_files(filepaths=files_to_upload)
    # the project starts when all participants have uploaded their data
    print(f"{username} uploaded data to project {project_id}")
    


if __name__ == "__main__":
    args = get_args()
   
    username = args.user
    project_id = args.project
    
    main(username=username, project_id=project_id)


