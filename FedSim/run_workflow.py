

from playwright.sync_api import sync_playwright, expect
from dotenv import load_dotenv



from FedSim.featurecloud_user import User, Coordinator
from utils import read_toml_config



class Clients: 

    def __init__(self, coordinator: str, participants: list[str]):
        self.coordinator = coordinator
        self.participants = participants
        self.clients = self._create_clients()


    def _create_clients(self) -> dict[str, User]:
        clients = {}
        # create users
        for p in self.participants:
            if p == self.coordinator:
                client = Coordinator(username=p)
            else:
                client = User(username=p)
            clients[client.username] = client
        return clients


    
    

def main():

    # read config file
    conf = read_toml_config("resources/config_svd.toml")
    # load credentials
    load_dotenv(dotenv_path="resources/.env", override=True)


    # create clients, dict of users
    clients = Clients(
        coordinator=conf['clients']['coordinator'],
        participants=conf['clients']['participants']
    )


    # start browser instance
    pw = sync_playwright().start()
    browser = pw.firefox.launch()

    # add browser to clients
    for c in clients.clients.values():
        c.setup_browser_context(browser=browser)


    for c in clients.clients.values():
        c.fc_login()
        c.verify_controller_running()



    
    # let the coordinator start the workflow
    # clients[clients.coordinator].start_workflow(proj_id=conf['project']['pid'])

    # upload data for each user



    browser.close()
    pw.stop()


main()







