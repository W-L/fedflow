import argparse

from featurecloud_api import User, Project



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a FeatureCloud project as coordinator")
    parser.add_argument("-u", "--user", help="Username for FeatureCloud login")
    parser.add_argument("-t", "--tool", help="Tool to use in project")
    parser.add_argument("-p", "--participants", help="The number of participants, i.e. number of tokens to create", type=int, default=0)
    args = parser.parse_args()
    return args


def main(username, tool, n_participants) -> None:
    user = User(username=username)
    new_proj = Project.from_tool(tool=tool, client=user.client)
    tokens = new_proj.create_project_tokens(n=n_participants)
    print()
    print(f"PROJECT: {new_proj.project_id}")
    for t in tokens:
        print(f"TOKEN: {t['token']}")
    
    
    

if __name__ == "__main__":
    args = get_args()
   
    username = args.user
    tool = args.tool
    n_participants = args.participants

    main(username=username, tool=tool, n_participants=n_participants)



