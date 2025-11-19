import argparse
import time


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
    # monitor the project run
    final_status = fcc.monitor_project()
    print(f"Project {project_id} status: {final_status}")
    time.sleep(5)
    # download outcome
    out_dir = 'results/'
    downloaded_files = fcc.download_outcome(out_dir=out_dir)
    print(f"Run finished with status {final_status}. Logs (& Results) downloaded to {out_dir}: \n{downloaded_files}")

    

if __name__ == "__main__":
    args = get_args()
   
    username = args.user
    project_id = args.project
    
    main(username=username, project_id=project_id)


