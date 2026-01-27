# Implementing Hostname-Based Server Access Restrictions on FSx ONTAP CIFS Shares

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5392138245/Implementing%20Hostname-Based%20Server%20Access%20Restrictions%20on%20FSx%20ONTAP%20CIFS%20Shares

**Created by:** Aravindan A on December 26, 2025  
**Last modified by:** Aravindan A on December 26, 2025 at 03:06 PM

---

FSx ONTAP Server Restriction - Implementation Steps
===================================================

Overview
--------

Implement hostname-based server access restrictions on FSx ONTAP CIFS shares using export policies by adding hostname-based rules to allow only specific servers access to CIFS shares.

Solutions Architecture
----------------------

This illustrates Amazon FSx ONTAP's hostname-based access control for CIFS shares. Two authorized servers for example (SCLRAPP01-LAX3 and SCLRAPP04-LAX3) can successfully mount the sclr\_test share because their hostnames match the export policy rules. Other servers are blocked due to no matching rules in the "server-restriction" export policy. The SVM enforces these policies at the volume level, providing granular access control based on client hostname resolution.

![FSx_Restriction_Architecture_Diagram(1).png](images/FSx_Restriction_Architecture_Diagram(1).png)

Access Flow Diagram:
--------------------

<https://healthedge.atlassian.net/wiki/spaces/CP1/whiteboard/5391941652>

Implementation Steps
--------------------

### 1. Connect to FSx ONTAP

Establish SSH connection to FSx ONTAP management interface using administrative credentials.  
This provides command-line access to configure export policies and CIFS settings.


```bash
ssh fsxadmin@<FSX-MANAGEMENT-IP>
```


### 2. Enable Export Policy Enforcement

Enable CIFS export policy enforcement which is disabled by default in FSx ONTAP.  
Advanced privilege mode is required to modify this critical security setting.


```bash
set -privilege advanced
vserver cifs options modify -vserver <SVM-NAME> -is-exportpolicy-enabled true
set -privilege admin
```


### 3. Create Export Policy

Create a named export policy container that will hold the server access rules.  
This policy will be applied to volumes to enforce hostname-based restrictions.


```bash
export-policy create -vserver <SVM-NAME> -policyname server-restriction
```


### 4. Configure Access Rules (Hostname-Based)

Add hostname-based rules to allow only specific servers access to CIFS shares.  
Each rule specifies a server hostname, protocol (CIFS), and read/write permissions.


```bash
export-policy rule create -vserver <SVM-NAME> -policyname server-restriction -ruleindex 1 -protocol cifs -clientmatch SCLRAPP01-LAX3 -rorule any -rwrule any
export-policy rule create -vserver <SVM-NAME> -policyname server-restriction -ruleindex 2 -protocol cifs -clientmatch SCLRAPP04-LAX3 -rorule any -rwrule any
```


### 5. Apply Policy to Volume

Assign the export policy to the target volume to enforce server restrictions.  
This replaces the default policy and activates hostname-based access control.


```bash
volume modify -vserver <SVM-NAME> -volume <VOLUME-NAME> -policy server-restriction
```


### 6. Configure CIFS Share Permissions

Remove default "Everyone" access and add specific user/group permissions for share-level security.  
This provides a second layer of security at the application level after export policy filtering.


```bash
vserver cifs share access-control delete -vserver <SVM-NAME> -share <SHARE-NAME> -user-or-group Everyone
vserver cifs share access-control create -vserver <SVM-NAME> -share <SHARE-NAME> -user-or-group "<DOMAIN>\<USERNAME>" -permission Full_Control
```


### 7. Test Access Control

Verify export policy rules work by testing allowed and blocked IP addresses using built-in commands.  
Note that check-access only accepts IP addresses, not hostnames, but tests the underlying policy logic.


```bash
vserver export-policy check-access -vserver <SVM-NAME> -volume <VOLUME-NAME> -client-ip <SCLRAPP01-IP> -protocol cifs -authentication-method sys -access-type read
vserver export-policy check-access -vserver <SVM-NAME> -volume <VOLUME-NAME> -client-ip <UNAUTHORIZED-IP> -protocol cifs -authentication-method sys -access-type read
```


### 8. Final Verification

Test actual CIFS connections from Windows servers to confirm restrictions are working in practice.  
This validates that hostname resolution and export policy enforcement work together correctly.

* **SCLRAPP01-LAX3**: Should connect successfully
* **SCLRAPP04-LAX3**: Should connect successfully
* **Other servers**: Should receive access denied

Verification Commands
---------------------


```bash
vserver cifs options show -vserver <SVM-NAME> -fields is-exportpolicy-enabled
export-policy rule show -vserver <SVM-NAME> -policyname server-restriction
volume show -vserver <SVM-NAME> -volume <VOLUME-NAME> -fields policy
vserver cifs share access-control show -vserver <SVM-NAME> -share <SHARE-NAME>
```


Requirements
------------

* Server hostnames must be resolvable by FSx ONTAP
* FSx ONTAP administrative access
* Advanced privilege mode access

Expected Results
----------------

* Only servers with matching hostnames can access restricted CIFS shares
* FSx ONTAP resolves hostnames to IPs during access evaluation
* Network-level security independent of user permissions