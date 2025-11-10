# Page snapshot

```yaml
- generic [ref=e6]:
  - generic [ref=e7]:
    - img [ref=e9]
    - heading "AWS DRS Orchestration" [level=1] [ref=e11]
    - paragraph [ref=e12]: Sign in to access the platform
  - alert [ref=e13]:
    - img [ref=e15]
    - generic [ref=e17]: User pool client 4lfcl1e2lrciv5s2ost1nnrdo0 does not exist.
  - generic [ref=e18]:
    - generic [ref=e19]:
      - generic [ref=e20]:
        - text: Username
        - generic [ref=e21]: "*"
      - generic [ref=e22]:
        - textbox "Username" [ref=e23]: drs-test-user@example.com
        - group:
          - generic: Username *
    - generic [ref=e24]:
      - generic [ref=e25]:
        - text: Password
        - generic [ref=e26]: "*"
      - generic [ref=e27]:
        - textbox "Password" [ref=e28]: TestUser123!
        - group:
          - generic: Password *
    - button "Sign In" [ref=e29] [cursor=pointer]: Sign In
  - generic [ref=e30]: Powered by AWS Cognito
```