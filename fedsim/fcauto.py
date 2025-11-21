import argparse

import fedsim.featurecloud_api as featurecloud_api



def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog='fcauto', description='FeatureCloud automation tool')
    sub = parser.add_subparsers(dest="cmd", required=True)

    # common arguments
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-u", "--user", help="Username on FeatureCloud")
    common.add_argument("-p", "--project", help="FeatureCloud project ID")
    
    # parsers for subcommands
    create = sub.add_parser(
        "create", 
        help="Create a new FeatureCloud project (as coordinator)", 
        parents=[common]
    )
    join = sub.add_parser(
        "join", 
        help="Join an existing FeatureCloud project",
        parents=[common]
    )
    monitor = sub.add_parser(
        "monitor", 
        help="Monitor a running FeatureCloud project", 
        parents=[common]
    )
    query = sub.add_parser(
        "query", 
        help="Query FeatureCloud project status",
        parents=[common]
    )
    contribute = sub.add_parser(
        "contribute", 
        help="Contribute data to a FeatureCloud project",
        parents=[common]
    )
    reset = sub.add_parser(
        "reset", 
        help="Reset a FeatureCloud project to status 'ready' ",
        parents=[common]
    )
    # TODO add download subcommand

    # arguments for project creation
    create.add_argument("-t", "--tool", help="Tool to use in project")
    create.add_argument("-n", "--num", help="Number of participant tokens to create",
                         type=int, default=0)
    # arguments to join a project
    join.add_argument("-t", "--token", help="Token to join project")
    # arguments for uploading data to a project
    contribute.add_argument("-d", "--data", help="Paths of data to contribute. Can be multiple arguments.", nargs='+')
    # monitor, query and reset have no additional arguments
    args = parser.parse_args()
    return args




def main():
    args = get_args()

    if args.cmd == "create":
        featurecloud_api.create_project_and_tokens(
            username=args.user,
            tool=args.tool,
            n_participants=args.num,
    )
    elif args.cmd == "join":
        featurecloud_api.join_project(
            username=args.user,
            token=args.token,
            project_id=args.project,
    )
    elif args.cmd == "monitor":
        featurecloud_api.monitor_project(
            username=args.user,
            project_id=args.project,
        )
    elif args.cmd == "query":
        featurecloud_api.query_project(
            username=args.user,
            project_id=args.project,
        )
    elif args.cmd == "contribute":
        featurecloud_api.contribute_data(
            username=args.user,
            project_id=args.project,
            data_list=args.data,
        )
    elif args.cmd == "reset":
        featurecloud_api.reset_project(
            username=args.user,
            project_id=args.project,
        )



if __name__ == "__main__":
    main()
    
    
    


