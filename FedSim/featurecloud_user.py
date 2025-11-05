import os
from typing import Iterable

from playwright.sync_api import sync_playwright, expect


class User:

    def __init__(self, username: str):
        self.username = username
        self.email = str(os.getenv(username))
        self.password = str(os.getenv(f"{username}_P"))
        assert self.email is not None, f"Environment variable {username} not set."
        assert self.password is not None, f"Environment variable {username}_P not set."
        

    def start_browser(self):
        self.pw = sync_playwright().start()
        self.browser = self.pw.firefox.launch()
        self.context = self.browser.new_context()


    def stop_browser(self):
        self.context.close()
        self.browser.close()
        self.pw.stop()


    def fc_login(self):
        page = self.context.new_page()
        page.goto("https://featurecloud.ai/account?p=login")
        # Fill in credentials
        page.fill('input[name="loginEmail"]', self.email)
        page.fill('input[name="loginPassword"]', self.password)
        page.get_by_role("button", name="\uf090 Log In").click()
        page.wait_for_load_state("networkidle")
        _ = page.screenshot(path=f"fc_login_{self.username}.png")


    def verify_controller_running(self):
        page = self.context.new_page()
        page.goto("https://featurecloud.ai/controller")
        # on the controller site, check that the requirements for computing are met
        expect(page.get_by_text('Online', exact=True)).to_be_visible()
        expect(page.get_by_text('Docker is available', exact=True)).to_be_visible()
        expect(page.get_by_text('Site is registered', exact=True)).to_be_visible()
        _ = page.screenshot(path=f"fc_controller_{self.username}.png")


    def upload_data(self, proj_id: str, file_paths):
        page = self.context.new_page()
        page.goto(f"https://featurecloud.ai/project/{proj_id}")
        # upload data to the project workflow
        page.locator('[id="upload"]').set_input_files(file_paths)
        # then another button appears to confirm upload
        page.get_by_role("button", name="Upload", exact=True).click()
        # TODO upload multiple files? or does the set_input_files handle that?

        # then another button appers to continue workflow
        page.get_by_role("button", name="Continue workflow", exact=True).click()
        page.get_by_role("button", name="Yes", exact=True).click()
        



class Coordinator(User):


    def start_workflow(self, proj_id: str):
        page = self.context.new_page()
        page.goto(f"https://featurecloud.ai/project/{proj_id}")
        page.get_by_role("button", name="\uf04b Start").click()
        page.wait_for_load_state("networkidle")
        


