import requests
import time

class Watcher:
    def __init__(self, repo, token, discord_webhook_url):
        self.repo = repo
        self.token = token
        self.discord_webhook_url = discord_webhook_url
        self.latest_commit_sha = None
        self.latest_pr_id = None
        self.latest_branches = set()  # Keep track of known branches

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

    def fetch_branches(self):
        url = f"https://api.github.com/repos/{self.repo}/branches"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return [branch['name'] for branch in response.json()]
        else:
            print(f"Error fetching branches: {response.status_code} - {response.text}")
            return []

    def format_file_changes(self, file_status, file_name):
        """Format file changes with rich text for Discord embed."""
        if file_status == "added":
            return f"+ {file_name}"  # Green text for added files
        elif file_status == "modified":
            return f"! {file_name}"  # Yellow/Orange text for modified files
        elif file_status == "removed":
            return f"- {file_name}"  # Red text for deleted files
        else:
            return f"{file_name}"  # Default format for other statuses

    def send_discord_embed(self, title, description, url, commit_message, files=None, author=None):
        formatted_files = "\n".join(files) if files else ""
        
        embed = {
            "embeds": [
                {
                    "type": "rich",
                    "title": title,
                    "description": f">>> {description}\n```diff\n{formatted_files}\n```",
                    "url": url,
                    "color": 0x4CAF50,  # Green for the embed color
                    "author": {
                        "name": author.get('name') if author else "Unknown Author",
                        "url": author.get('url') if author else "",
                        "icon_url": author.get('icon_url') if author else ""
                    },
                    "fields": [
                        {
                            "name": "`Commit SHA`",
                            "value": f"`{self.latest_commit_sha}`",
                            "inline": True
                        },
                        {
                            "name": "Commit Message",
                            "value": f"```fix\n{commit_message}\n```",
                            "inline": False
                        }
                    ],
                    "footer": {
                        "text": "GitHub Notifications"
                    }
                }
            ]
        }
        
        response = requests.post(self.discord_webhook_url, json=embed)
        
        if response.status_code == 204:
            print("Embed notification sent successfully.")
        else:
            print(f"Failed to send embed notification: {response.status_code} - {response.text}")

    def check_for_changes(self):
    # Check for new commits
        commits = self.fetch_commits()
        
        if commits:
            if 'sha' in commits[0]:
                new_commit_sha = commits[0]['sha']
                if new_commit_sha != self.latest_commit_sha:
                    self.latest_commit_sha = new_commit_sha
                    commit_url = commits[0]['html_url']
                    commit_message = commits[0]['commit']['message']
                    author_info = {
                        "name": commits[0]['commit']['author']['name'],
                        "url": commits[0]['author']['html_url'] if commits[0].get('author') else "",
                        "icon_url": commits[0]['author']['avatar_url'] if commits[0].get('author') else ""
                    }
                    
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
                            files.append(self.format_file_changes(file_status, file_name))
                        
                        # Check if files list is empty
                        if not files:
                            files.append("What an idiot xd!")

                        self.send_discord_embed(
                            title="New Commit to Repository",
                            description=f"There's been **{len(files)}** file changes to [{self.repo}]({commit_url})",
                            url=commit_url,
                            commit_message=commit_message,
                            files=files,
                            author=author_info
                        )
                    else:
                        print(f"Error fetching commit details: {commit_details.status_code} - {commit_details.text}")

            else:
                print("No SHA key found in commits.")
        else:
            print("No commits found.")


            # Check for new pull requests
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
                            url=pr_url,
                            commit_message="",  # No commit message for PRs
                            files=[]
                        )
                        print(f"Latest PR ID: {self.latest_pr_id}")
                else:
                    print("Latest PR does not have an 'id' key.")
            else:
                print("No pull requests found.")

        # Check for new branches
        branches = self.fetch_branches()
        new_branches = set(branches) - self.latest_branches  # Find new branches
        
        if new_branches:
            for branch in new_branches:
                self.send_discord_embed(
                    title="New Branch Created",
                    description=f"A new branch **{branch}** has been created in [{self.repo}](https://github.com/{self.repo}/tree/{branch}).",
                    url=f"https://github.com/{self.repo}/tree/{branch}",
                    commit_message="",  # No commit message for branch creation
                    files=[],
                    author=None
                )
            self.latest_branches.update(new_branches)

