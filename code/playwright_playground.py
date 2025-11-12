from playwright.sync_api import sync_playwright


pw = sync_playwright().start()
browser = pw.firefox.launch(headless=False)
context = browser.new_context()
page = context.new_page()


page.goto("https://featurecloud.ai/account?p=login")
# Fill in credentials
page.fill('input[name="loginEmail"]', 'p73wzaml9@mozmail.com')
page.fill('input[name="loginPassword"]', ',:~n8E#;g*Xj@eE')
page.get_by_role("button", name="\uf090 Log In").click()
page.wait_for_load_state("networkidle")


# go to project page and start wf
page.goto("https://featurecloud.ai/project/17263")
page.get_by_role("button", name="\uf04b Start").click()


# this actually works to select a file
page.locator('[id="upload"]').set_input_files('data/testing.txt')
# then another button appears to confirm upload
page.get_by_role("button", name="Upload", exact=True).click()
# then another button appers to continue workflow
page.get_by_role("button", name="Continue workflow", exact=True).click()
page.get_by_role("button", name="Yes", exact=True).click()
# then we wait for other participants to upload their data


# the page for upload looks and works just the same for the participants
# at some point the workflow will just continue running, hopefully
# so for each participant do the same as above




browser.close()
pw.stop()

