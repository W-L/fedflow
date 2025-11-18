import argparse

from featurecloud_api import User, Project



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a FeatureCloud project as coordinator")
    parser.add_argument("-u", "--user", help="Username for FeatureCloud login")
    parser.add_argument("-t", "--token", help="Token to join the project")
    parser.add_argument("-p", "--project", help="The project ID to join")
    args = parser.parse_args()
    return args


def main(username, token, project_id) -> None:
    user = User(username=username)
    joined_proj = Project.from_token(token=token, project_id=project_id, client=user.client)
    print(f"Joined project: {joined_proj.project_id}")
    
    

if __name__ == "__main__":
    args = get_args()
   
    username = args.user
    token = args.token
    project_id = args.project

    main(username=username, token=token, project_id=project_id)



