import requests
import time

class Watcher:
    def __init__(self, repo, token, discord_webhook_url):
        self.repo = repo
        self.token = token
        self.discord_webhook_url = discord_webhook_url
        self.latest_commit_sha = None
        self.latest_pr_id = None

    def fetch_commits(self):
        url = f"https://api.github.com/repos/{self.repo}/commits"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching commits: {response.status_code} - {response.text}")
            return []

    def fetch_pull_requests(self):
        url = f"https://api.github.com/repos/{self.repo}/pulls"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching pull requests: {response.status_code} - {response.text}")
            return []

    def send_discord_embed(self, title, description, url, files=None):
        embed = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "url": url,
                    "color": 3066993,  # Color for the embed (in decimal)
                    "footer": {
                        "text": "GitHub Notifications"
                    }
                }
            ]
        }
        
        if files:
            file_changes = "\n".join(files)
            embed['embeds'][0]['fields'] = [
                {
                    "name": "File Changes",
                    "value": file_changes,
                    "inline": False
                }
            ]
        
        response = requests.post(self.discord_webhook_url, json=embed)
        
        if response.status_code == 204:
            print("Embed notification sent successfully.")
        else:
            print(f"Failed to send embed notification: {response.status_code} - {response.text}")

    def check_for_changes(self):
        commits = self.fetch_commits()
        
        if commits:
            if 'sha' in commits[0]:  # Check if 'sha' key exists
                new_commit_sha = commits[0]['sha']
                if new_commit_sha != self.latest_commit_sha:
                    self.latest_commit_sha = new_commit_sha
                    commit_url = commits[0]['html_url']
                    # Fetch detailed commit information
                    commit_details = requests.get(commits[0]['url'], headers={
                        "Authorization": f"token {self.token}",
                        "Accept": "application/vnd.github.v3+json"
                    })

                    if commit_details.status_code == 200:
                        commit_data = commit_details.json()
                        files = []
                        for file in commit_data.get('files', []):
                            file_status = file.get('status')
                            file_name = file.get('filename')
                            files.append(f"{file_status.capitalize()}: {file_name}")
                        
                        self.send_discord_embed(
                            title="New Commit",
                            description=f"Commit SHA: {new_commit_sha}",
                            url=commit_url,
                            files=files
                        )
                    else:
                        print(f"Error fetching commit details: {commit_details.status_code} - {commit_details.text}")

            else:
                print("No SHA key found in commits.")

        else:
            print("No commits found.")

        pull_requests = self.fetch_pull_requests()
        
        if pull_requests:
            if 'id' in pull_requests[0]:  # Check if 'id' key exists
                new_pr_id = pull_requests[0]['id']
                if new_pr_id != self.latest_pr_id:
                    self.latest_pr_id = new_pr_id
                    pr_title = pull_requests[0]['title']
                    pr_url = pull_requests[0]['html_url']
                    self.send_discord_embed(
                        title="New Pull Request",
                        description=pr_title,
                        url=pr_url
                    )
                    print(f"Latest PR ID: {self.latest_pr_id}")
            else:
                print("Latest PR does not have an 'id' key.")
        else:
            print("No pull requests found.")

if __name__ == "__main__":
    repo = "1stijn/1stijn"  # Replace with your GitHub repository
    token = "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"  # Replace with your GitHub token
    discord_webhook_url = "https://discord.com/api/webhooks/1290363382611968002/nDeOF1RG4jcPKnxM7PD_2RSJSuNenv8wlsEQlKEQrwkYlK4lWNPDZTlE1yrFxRqV9254"  # Replace with your Discord webhook URL
    
    watcher = Watcher(repo, token, discord_webhook_url)
    
    while True:
        watcher.check_for_changes()
        time.sleep(30)  # Sleep for 30 seconds before checking again