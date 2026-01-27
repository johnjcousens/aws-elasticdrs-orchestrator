# Runbook - Cloning GitHub Repository

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4940824608/Runbook%20-%20Cloning%20GitHub%20Repository

**Created by:** Chris Falk on July 17, 2025  
**Last modified by:** Chris Falk on July 17, 2025 at 07:47 PM

---

These instructions are for a Mac or Linux machine:

1. Generate an SSH key: `ssh-keygen -t ed25519 -C "healthedge-github" -f healthedge-github`
2. Add an SSH key in your GitHub settings and populate it with the content from the public key file `healthedge-github.pub`; save
3. Select "Configure SSO" and authorize for HE-Core
4. Clone the repository specifying your key one-time: `GIT_SSH_COMMAND="ssh -i ~/.ssh/healthedge-github" git clone git@github.com:HE-Core/platform.devops.aws.lza-config.git`
5. Change directory into the cloned repository directory and set a local config to use your private key for this repo only: `git config core.sshCommand "ssh -i ~/.ssh/healthedge-github"`