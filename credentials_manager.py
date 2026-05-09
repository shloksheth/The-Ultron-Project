import json
import os

class CredentialManager:
    def __init__(self, filepath="credentials.json"):
        self.filepath = filepath
        self.creds = self._load()

    def _load(self):
        if os.path.exists(self.filepath):
            with open(self.filepath, "r") as f:
                return json.load(f)
        return {}

    def save_creds(self, site, username, password):
        self.creds[site] = {"username": username, "password": password}
        with open(self.filepath, "w") as f:
            json.dump(self.creds, f)

    def get_creds(self, site):
        return self.creds.get(site)

if __name__ == "__main__":
    cm = CredentialManager()
    cm.save_creds("deltamath", "testuser", "testpass")
    print(cm.get_creds("deltamath"))
