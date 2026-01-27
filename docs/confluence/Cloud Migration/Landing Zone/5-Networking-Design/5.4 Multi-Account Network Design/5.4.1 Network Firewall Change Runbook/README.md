# 5.4.1 Network Firewall Change Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5176951397/5.4.1%20Network%20Firewall%20Change%20Runbook

**Created by:** Chris Falk on October 17, 2025  
**Last modified by:** Chris Falk on October 22, 2025 at 12:49 PM

---

AWS Network Firewall Change Management Runbook
==============================================

Overview
--------

**Purpose:** Step-by-step procedures for safely implementing firewall rule changes

**Scope:** Covers all four regions (us-east-1, us-east-2, us-west-1, us-west-2)

**Audience:** Network operations, security engineers, DevOps teams

---

Before You Begin
----------------

### Prerequisites

* Access to the LZA configuration repository
* Understanding of [Suricata rule syntax](https://docs.suricata.io/en/suricata-6.0.9/rules/intro.html)
* Knowledge of the affected application/service
* Change ticket number (if required)

### Required Information

Before making any firewall changes, gather:

* Source and destination IP addresses/networks
* Protocols and ports required
* Business justification
* Expected traffic volume
* Affected regions

---

Rule Writing Best Practices
---------------------------

### Suricata Rule Syntax


```
action protocol source port direction destination port (options)
pass ip any any -> any 22 (msg:"Allow ssh"; flow:established; ssh.proto; sid:10001;)
```


**Actions:**

* `pass` - Allow traffic (most common)
* `drop` - Block traffic silently
* `reject` - Block traffic actively
* `alert` - Log (for monitoring)

**Key Options:**

* `msg:"Description"` - Human-readable description (required)
* `sid:XXXXX` - Unique signature ID (required)
* `flow:established` - For TCP connections
* `flow:to_server` - For client-to-server traffic to avoid conflicts between rules at different layers (L4/L7, e.g. tcp 443 vs `tls` keyword)

### SID Numbering Convention

| Range | Purpose |
| --- | --- |
| 10001-19999 | Common rules (all business units) |
| 20001-29999 | HRP-specific rules |
| 30001-39999 | Guiding Care-specific rules |
| 40001-49999 | Wellframe-specific rules |
| 50001-59999 | Source-specific rules |

**Finding the next available SID:**

1. Review existing rules in `firewall-rules/BaselineFirewallRuleGroup.txt`
2. Use the next sequential number in the appropriate range, or if inserting, renumber existing rules
3. Document the SID in your change ticket

### Variable Usage

**Use IP and Port variables instead of hardcoded values when possible**

The same rules file is deployed identically to all four regional firewalls. Some variables are region-specific, and others are the same in all regions. Review the `network-config.yaml` in the AWS Landing Zone Accelerator repository for the definitions of the regional AWS Network Firewall Rule Groups and their variables/values.

✅ **Good:**


```
pass tcp $HRP_WORKLOAD_NET_DEV any -> $HRP_DATA_CENTERS $HRP_APP_TRAFFIC (flow:established; msg:"HRP app traffic"; sid:20050;)
```


❌ **Bad:**


```
pass tcp 10.192.224.0/19 any -> 10.51.0.0/16 [80,443,1433] (flow:established; msg:"HRP app traffic"; sid:20050;)
```


**Common Variables:**

| Variable | Description |
| --- | --- |
| `$WORKLOAD_NET` | AWS workload subnets (region-specific) |
| `$DATA_CENTERS` | All on-premises networks |
| `$ENDPOINTS_NET` | VPC endpoint subnets |
| `$HRP_JUMP_SOURCES` | HRP bastion hosts |
| `$GC_JUMP_SOURCES` | Guiding Care bastion hosts |
| `$WEB` | Ports 80, 443 |
| `$DNS` | Port 53 |

The full list of variables is available in the AWS Network Firewall console by reviewing the Rule Group

### Rule Placement Guidelines

**Order matters!** Rules are evaluated in strict order:

1. **Geo-blocking** (SID 10001) - Always first
2. **Specific deny rules** - Block known bad traffic
3. **Specific allow rules** - Permit required traffic
4. **General allow rules** - Broader permissions
5. **Default deny** - Firewall is set to drop by default, but this is not required in the rules file - it is implied

**Example ordering:**


```
# 1. Block countries (already at top)
drop ip any any -> any any (msg:"Drop blocked countries"; sid:10001; geoip:...;)

# 2. Specific application rule
pass tcp $HRP_WORKLOAD_NET_DEV any -> 10.14.252.16 $HRP_NEXUS (flow:established; msg:"Nexus artifact registry"; sid:20009;)

# 3. General web traffic
pass tls $WORKLOAD_NET any -> $WORKLOAD_NET 443 (msg:"Web traffic"; sid:10003; flow:to_server;)
```


---

Change Procedure
----------------

### Step 1: Analyze the Request

* Identify source and destination networks
* Determine required protocols and ports
* Check if existing rules already permit the traffic
* Verify business justification

### Step 2: Write the Rule

**Template for new rule:**


```
pass [protocol] [source] any -> [destination] [port] (flow:established; msg:"[Description]"; sid:[XXXXX];)
```


**Example - Allow new monitoring tool:**


```
pass tcp $HRP_WORKLOAD_NET_DEV any -> 10.51.20.50 8080 (flow:established; msg:"New monitoring dashboard"; sid:20050;)
```


**Regional Considerations:**

* Rules are defined once but deployed to all regions
* Use region-specific variables (e.g., `$HOME_NET`, `$WORKLOAD_NET`)
* Variables are automatically populated per region in `network-config.yaml`

### Step 3: Update Configuration Files

**File to modify:** `firewall-rules/BaselineFirewallRuleGroup.txt`

1. Open the file in your editor
2. Find the appropriate section (Common/HRP/GC)
3. Add your rule in the correct position
4. Ensure proper formatting (no extra spaces, correct syntax)

**Example addition:**


```
# HRP section
pass tcp $HRP_JUMP_SOURCES any -> [$HRP_WORKLOAD_NET_DEV,$HRP_WORKLOAD_NET_SHARED] $HRP_JUMP_PORTS (flow:established; msg:"Access from HRP Bastions"; sid:20001;)
pass tcp $HRP_WORKLOAD_NET_DEV any -> 10.51.20.50 8080 (flow:established; msg:"New monitoring dashboard"; sid:20050;)  # <-- NEW RULE
```


### Step 4: Validate Syntax

**Common syntax errors to avoid:**

| Error | Correct |
| --- | --- |
| `(msg:"test" sid:1000;)` ❌ missing semicolon | `(msg:"test"; sid:1000;)` ✅ |
| `(msg:"test"; sid: 1000;)` ❌ extra space in sid option | `(msg:"test"; sid:1000;)` ✅ |
| `<->` (bidirectional) | `->` (unidirectional) |
| `msg:test` ❌ | `msg:"test"` ✅ |
| Duplicate SIDs | Unique SIDs |
| Malformed CIDR blocks | Valid CIDR notation |
| Brackets enclose lists | `[$VAR1,$VAR2]` or `[$PORTS1,$PORTS2]` |

**Validation checklist:**

* Rule follows correct syntax format
* SID is unique and in correct range
* Message is descriptive and quoted
* Variables are properly referenced with `$`
* Ports are defined in port sets or as numbers
* Flow direction is specified for TCP rules

### Step 5: Deploy Change

**Recommended testing approach:**

1. **Deploy to development first:**

   * Commit changes to a feature branch, push to GitHub, open a Pull Request
   * Merge requires security review and approval
   * Ensure LZA pipeline is not executing before merging
   * Merge triggers deploy via LZA pipeline to production firewalls
   * Monitor firewall alert logs after change
2. **Verify traffic flow:**

   * Check [CloudWatch Logs Insights](https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights) for firewall alert and flow logs
   * Confirm application connectivity
   * Review alert logs for unexpected blocks
   * Consider an identical rule above your new rule with an `alert` keyword to force logging of the traffic before `pass` allows the flow (additional `sid:` required!)
3. **Use this AWS CloudWatch Logs Insights query to see firewall drops or use the query generator to create your own:**

   
```
fields @timestamp, event.src_ip, event.dest_ip, event.src_port, event.dest_port, event.proto, event.verdict.action 
| filter event.verdict.action = "drop" 
| sort @timestamp desc
```


### Emergency Changes

For emergency changes, the rules file can be edited directly in the AWS Network Firewall Rule Group console. **IMPORTANT: When the pipeline runs, if there are changes to the firewall rules in the repository they will OVERWRITE whatever is in the network firewall configuration, both ipSets/portSets and rules themselves. Make sure you commit any emergency changes made in console to the repo as soon as possible after resolving the incident, then run the pipeline and validate the changes were implemented successfully.**

1. Open the AWS VPC Console and navigate to AWS Network Firewall Rule Groups on the left
2. Switch to the region where you need to make the change
3. Copy the contents of the rule file from the LZA repository or the console to a local text editor
4. Make your rule changes
5. In the AWS console, edit the rules
6. Paste the new edited rules file contents back into the console and save the change
7. Repeat the edit/paste for other regions if needed
8. Ensure the repository is updated with the changes as soon as possible and re-deployed

### **Emergency Changes**

* Revert the commit in Git
* Re-run LZA pipeline
* Changes revert within 10-15 minutes

---

Common Scenarios
----------------

### Scenario 1: Allow New Application Traffic

**Use case:** New application needs to connect to database

**Steps:**

1. Identify source (application subnet) and destination (database subnet)
2. Determine port (e.g., 1433 for SQL Server)
3. Write rule:


```
pass tcp $HRP_WORKLOAD_NET_DEV any -> $HRP_AWS_DB_SUBNETS_DEV 1433 (flow:established; msg:"New app to database"; sid:20051;)
```


### Scenario 2: Allow Bastion/Jump Host Access

**Use case:** New jump host needs access to workload

**Steps:**

1. Add IP to appropriate jump source variable in `network-config.yaml`
2. Existing rules automatically include new IP
3. No rule changes needed if using `$HRP_JUMP_SOURCES` or `$GC_JUMP_SOURCES`

### Scenario 3: Allow Third-Party SaaS Integration

**Use case:** Application needs to reach external SaaS service

**Steps:**

1. Get IP ranges or domain from vendor
2. Add to appropriate variable or use specific IPs
3. Write rule:


```
pass tls $HRP_WORKLOAD_NET_DEV any -> [52.1.2.3,52.1.2.4] 443 (msg:"SaaS vendor API"; sid:20052;)
```


### Scenario 4: Temporary Rule for Troubleshooting

**Use case:** Need to temporarily allow all traffic for debugging

**Steps:**

1. Add alert rule (doesn't block, just logs):


```
alert tcp $HRP_WORKLOAD_NET_DEV any -> 10.51.20.100 any (msg:"Troubleshooting server X"; sid:20053;)
```


2. Review logs to see what ports are being used
3. Replace with specific pass rule
4. Remove alert rule

### Scenario 5: Block Specific Traffic

**Use case:** Need to block traffic to compromised host

**Steps:**

1. Add drop rule near the top (after geo-blocking):


```
drop ip any any -> 10.192.50.100 any (msg:"Block compromised host"; sid:10100;)
```


2. Place before any pass rules that might match
3. Monitor for attempts in logs

---

Troubleshooting
---------------

### Traffic Not Flowing After Rule Addition

**Check:**

1. Rule syntax is correct (no errors in LZA deployment)
2. Rule is placed before more general rules that might match first
3. Variables are correctly defined and utilized for the region
4. Source/destination addresses are correct
5. Flow direction is appropriate (`flow:established` for most TCP)

**Debug steps:**

1. Check CloudWatch Logs Insights for drops
2. Look for alert rules that might indicate the traffic
3. Verify rule SID appears in logs
4. Check if a more specific deny rule exists above your rule

### Rule Not Matching Expected Traffic

**Common causes:**

1. Variable doesn't include the actual IP range
2. Port set doesn't include the required port
3. Protocol mismatch (TCP vs UDP)
4. Direction is wrong (to\_server vs from\_server)

**Fix:**

1. Review variable definitions in `network-config.yaml`
2. Add missing IPs to appropriate variable
3. Verify protocol with packet capture or application documentation

### Performance Issues After Rule Addition

**Symptoms:**

* Increased latency
* Packet drops
* High CPU on firewall

**Resolution:**

1. Review rule complexity (avoid regex in high-traffic rules)
2. Ensure variables are used (more efficient than lists)
3. Place most-used rules higher in the list
4. Consider rule group capacity (currently 3000)

---

Best Practices Summary
----------------------

### DO ✅

* Use variables instead of hardcoded IPs
* Write descriptive messages
* Test in dev/non-prod first
* Use unique SIDs in the correct range
* Document the business justification
* Place specific rules before general rules
* Use `flow:established` for TCP connections
* Monitor logs after deployment

### DON'T ❌

* Hardcode IP addresses when variables exist
* Reuse SIDs
* Skip testing in non-production
* Use overly broad rules (e.g., `any any -> any any`)
* Forget to specify flow direction for TCP
* Deploy directly to production
* Leave temporary troubleshooting rules in place
* Modify rules without a change ticket

---

Quick Reference
---------------

### Rule Template


```
pass tcp $SOURCE_VAR any -> $DEST_VAR $PORT_VAR (flow:established; msg:"Description"; sid:XXXXX;)
```


### Common Patterns


```
# Web traffic
pass tls $WORKLOAD_NET any -> $INTERNET 443 (msg:"HTTPS outbound"; sid:XXXXX;)

# Database access
pass tcp $APP_NET any -> $DB_NET [1433,1521,5432] (flow:established; msg:"DB access"; sid:XXXXX;)

# Jump host access
pass tcp $JUMP_SOURCES any -> $WORKLOAD_NET [22,3389] (flow:established; msg:"Admin access"; sid:XXXXX;)

# Monitoring
pass tcp $WORKLOAD_NET any -> $MONITORING_NET [161,162] (flow:established; msg:"SNMP monitoring"; sid:XXXXX;)

# Active Directory
pass tcp $WORKLOAD_NET any -> $AD_SERVERS $AD_TCP (flow:established; msg:"AD authentication"; sid:XXXXX;)
pass udp $WORKLOAD_NET any -> $AD_SERVERS $AD_UDP (msg:"AD DNS/Kerberos"; sid:XXXXX;)

# Storage protocols
pass tcp $WORKLOAD_NET any -> $STORAGE_NET $SMB_TCP (flow:established; msg:"SMB file access"; sid:XXXXX;)
pass tcp $WORKLOAD_NET any -> $STORAGE_NET $NFS_TCP (flow:established; msg:"NFS file access"; sid:XXXXX;)
```


### File Locations

| File | Purpose |
| --- | --- |
| `firewall-rules/BaselineFirewallRuleGroup.txt` | Suricata rules |
| `network-config.yaml` | Variable definitions (under `centralNetworkServices.networkFirewall.rules[].ruleGroup.ruleVariables`) |
| CloudWatch Logs | Example: `AWSAccelerator-NetworkVpcEndpointsStack-639966646465-us-east-1-NfwUsEast1AlertLogGroup14469A3E-1K4UjjSgsqy6` |

### Useful Commands


```
# Search for a specific SID in rules
grep "sid:20050" firewall-rules/BaselineFirewallRuleGroup.txt

# Find the highest SID in a range
grep -oP 'sid:\d+' firewall-rules/BaselineFirewallRuleGroup.txt | grep -oP '\d+' | sort -n | tail -1

# Validate rule syntax (basic check)
grep -E "^(pass|drop|alert)" firewall-rules/BaselineFirewallRuleGroup.txt
```


---

Additional Resources
--------------------

* [AWS Network Firewall Documentation](https://docs.aws.amazon.com/network-firewall/)
* [Suricata Rule Examples](https://docs.aws.amazon.com/network-firewall/latest/developerguide/suricata-examples.html)
* [Suricata Rules Documentation](https://docs.suricata.io/en/latest/rules/intro.html)
* [AWS Network Firewall Best Practices](https://aws.github.io/aws-security-services-best-practices/guides/network-firewall/)

---

Contact Information
-------------------

For questions or assistance:

* **Network Operations Team:** [Contact details]
* **Security Team:** [Contact details]
* **Emergency Escalation:** [Contact details]

---

*Last Updated: 2025.10.17* *by* [*chris.falk@healthedge.com*](mailto:chris.falk@healthedge.com)