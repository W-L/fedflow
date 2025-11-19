import argparse

from featurecloud_api import User, Project



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a FeatureCloud project as coordinator")
    parser.add_argument("-u", "--user", help="Username for FeatureCloud login")
    parser.add_argument("-p", "--project", help="project ID")
    args = parser.parse_args()
    return args


def main(username, project_id) -> None:
    user = User(username=username)
    proj = Project.from_project_id(project_id=project_id, client=user.client)    
    proj.reset_project()
    
    
if __name__ == "__main__":
    args = get_args()
    username = args.user
    project_id = args.project
    
    main(username=username, project_id=project_id)


