import csv
import os
import requests
import re
from datetime import datetime, timedelta

# Read GitHub token
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

headers = {'Authorization': f'token {GITHUB_TOKEN}'}
base_url = 'https://api.github.com'
target = 'wikimedia'

# Puppet file extensions
puppet_extensions = ['.pp', '.erb', '.epp']

# Fetch all repositories from target organzation.


def get_repositories(org):
    repos = []
    page = 1
    while True:
        url = f'{base_url}/orgs/{org}/repos?page={page}&per_page=100'
        response = requests.get(url, headers=headers)
        print(f"Requesting repositories: {org}, Page: {page}, Status Code: {response.status_code}")
        if response.status_code == 403:
            print("Rate limit exceeded.")
            break
        if response.status_code != 200:
            print(f"Error getting repositories: {response.text}")
            break
        try:
            page_repos = response.json()
            if not page_repos:
                break
            repos.extend(page_repos)
            page += 1
        except ValueError:
            print("Error parsing JSON response")
            break
    return repos

# get all files in the specified repository


def get_repo_files(repo):
    url = f'{base_url}/repos/{repo["full_name"]}/git/trees/{repo["default_branch"]}?recursive=1'
    response = requests.get(url, headers=headers)
    print(f"Requesting files for repo: {repo['full_name']}, Status Code: {response.status_code}")
    if response.status_code == 403:
        print('Rate limit exceeded or insufficient permissions.')
        return []
    if response.status_code != 200:
        print(f"Error fetching repo files: {response.text}")
        return []
    try:
        return response.json().get('tree', [])
    except ValueError:
        print(f"Error for repo: {repo['full_name']}")
        return []

# Fetch all commit messages for the specified repository.


def get_commit_messages(repo):
    url = f'{base_url}/repos/{repo["full_name"]}/commits'
    response = requests.get(url, headers=headers)
    print(f"Requesting commits for repo: {repo['full_name']}, Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Rate limit exceeded or insufficient permissions.")
        return []
    if response.status_code != 200:
        print(f"Error getting commits: {response.text}")
        return []
    try:
        commits = response.json()
        if isinstance(commits, list):
            return commits
        else:
            print("Bad format for commits response")
            return []
    except ValueError:
        print(f"Error getting JSON response for repo: {repo['full_name']}")
        return []

# Fetch all files modified in the specified commit.


def get_commit_files(repo, sha):
    url = f'{base_url}/repos/{repo["full_name"]}/commits/{sha}'
    response = requests.get(url, headers=headers)
    print(f"Requesting commit files for repo: {repo['full_name']}, Commit SHA: {sha}, Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Rate limit exceeded.")
        return []
    if response.status_code != 200:
        print(f"Error fetching commit files: {response.text}")
        return []
    try:
        return response.json().get('files', [])
    except ValueError:
        print(f"Error getting JSON response for commit: {sha} in repo: {repo['full_name']}")
        return []

# Fetch the summary of the specified issue.


def get_issue_summary(repo, issue_number):
    url = f'{base_url}/repos/{repo["full_name"]}/issues/{issue_number}'
    response = requests.get(url, headers=headers)
    print(f"Requesting issue summary for issue: {issue_number} in repo: {repo['full_name']}, Status Code: {response.status_code}")
    if response.status_code == 403:
        print("Rate limit exceeded or insufficient permissions.")
        return ''
    if response.status_code != 200:
        print(f"Error getting issue summary: {response.text}")
        return ''
    try:
        return response.json().get('title', '')
    except ValueError:
        print(f"Error getting JSON response for issue: {issue_number} in repo: {repo['full_name']}")
        return ''

# Filter repositories based on the presence of Puppet files.


def filter_repositories(repos):
    filtered_repos = []
    for repo in repos:
        print(f"Processing repo: {repo.get('full_name', 'Unknown')}")
        if isinstance(repo, dict) and not repo.get('private', True) and repo.get('size', 0) > 0:
            files = get_repo_files(repo)
            puppet_files = [f for f in files if any(
                f['path'].endswith(ext) for ext in puppet_extensions)]
            other_files = [f for f in files if not any(
                f['path'].endswith(ext) for ext in puppet_extensions)]
            print(f"Repo: {repo['full_name']}, Puppet files: {len(puppet_files)}, Other files: {len(other_files)}")
            if len(puppet_files) / len(other_files) >= 0.11:
                commits = get_commit_messages(repo)
                recent_commits = [c for c in commits if isinstance(c, dict) and datetime.strptime(
                    c['commit']['author']['date'], '%Y-%m-%dT%H:%M:%SZ') > datetime.now() - timedelta(days=30)]
                print(f"Repo: {repo['full_name']}, Recent commits: {len(recent_commits)}")
                filtered_repos.append(repo)
    return filtered_repos

# Extract commit messages and append issue summaries if present.


def extract_commit_data(repo):
    commits = get_commit_messages(repo)
    commit_data = []
    for commit in commits:
        sha = commit['sha']
        commit_files = get_commit_files(repo, sha)
        print(f"Commit SHA: {sha}, Files: {commit_files}")
        if any(file['filename'].endswith(ext) for file in commit_files for ext in puppet_extensions):
            message = commit['commit']['message']
            issue_number = re.search(r'#(\d+)', message)
            if issue_number:
                issue_summary = get_issue_summary(repo, issue_number.group(1))
                message += f' {issue_summary}'
            for file in commit_files:
                if any(file['filename'].endswith(ext) for ext in puppet_extensions):
                    commit_data.append(
                        (repo['full_name'], file['filename'], message))
    return commit_data


# Main function to fetch, filter, and process repositories and commit data.
def main():
    org = target
    repos = get_repositories(org)
    print(f"Total repositories fetched: {len(repos)}")
    filtered_repos = filter_repositories(repos)
    print(f"Total filtered repositories: {len(filtered_repos)}")
    with open('wikimedia_commit_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Repository', 'File', 'Commit Message']
        writer = csv.DictWriter(
            csvfile, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for repo in filtered_repos:
            commit_data = extract_commit_data(repo)
            for repo_name, file_name, message in commit_data:
                writer.writerow(
                    {'Repository': repo_name, 'File': file_name, 'Commit Message': message})


if __name__ == '__main__':
    main()