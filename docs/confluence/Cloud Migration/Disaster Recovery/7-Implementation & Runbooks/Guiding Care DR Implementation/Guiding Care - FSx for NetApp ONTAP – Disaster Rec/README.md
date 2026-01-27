# Guiding Care - FSx for NetApp ONTAP – Disaster Recovery Runbook

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5306581244/Guiding%20Care%20-%20FSx%20for%20NetApp%20ONTAP%20%E2%80%93%20Disaster%20Recovery%20Runbook

**Created by:** Alex Dixon on December 04, 2025  
**Last modified by:** Chris Falk on December 18, 2025 at 08:16 PM

---

**1. Purpose**
--------------

This runbook provides the operational steps required to perform **failover** and **failback** of FSx for NetApp ONTAP volumes between the primary AWS region and the DR region using SnapMirror. The procedures align with the customer’s existing:

* CDK deployment patterns
* AD-joined SVM model
* SMB share creation workflow via ONTAP CLI
* Security and routing architecture based on AWS Transit Gateway

This document assumes that the DR filesystem, SVM, and destination volumes have been deployed through CDK and that SnapMirror relationships have been established and initialized.

---

**2. Preconditions**
--------------------

Before failover or failback, confirm:

### **2.1 Infrastructure**

* DR filesystem is **Available**
* DR SVM exists and is AD-joined if SMB is used
* DR volumes exist with matching names and junction paths
* EC2 management instance can SSH to FSxN management endpoint

### **2.2 Networking**

* Transit Gateway routing is functional between regions
* Security groups allow:

  + TCP **11104–11105** (cluster peering)
  + TCP **10000** (SnapMirror)
  + AD/DNS ports if SMB authentication will be used

### **2.3 SnapMirror Health**

Run:


```
snapmirror show -fields status,lag-time,last-transfer-end-timestamp
```


SnapMirror must be in a **Healthy** state before initiating failover.

---

**3. Failover Procedure**
=========================

*Primary Region → DR Region*

Failover activates the DR filesystem by promoting replicated volumes to read/write and redirecting applications to the DR region.

---

**Step 1 — Quiesce Application Writes (If Possible)**
-----------------------------------------------------

Notify application teams. Halt new writes or stop dependent services to minimize divergence.

---

**Step 2 — Perform Final Replication Update**
---------------------------------------------


```
snapmirror update -destination-path <dr_svm>:<dr_volume>
```


Verify update completion:


```
snapmirror show -destination-path <dr_svm>:<dr_volume> -fields last-transfer-end-timestamp
```


---

**Step 3 — Quiesce the SnapMirror Relationship**
------------------------------------------------


```
snapmirror quiesce -destination-path <dr_svm>:<dr_volume>
```


---

**Step 4 — Break SnapMirror (Promote DR Copy)**
-----------------------------------------------


```
snapmirror break -destination-path <dr_svm>:<dr_volume>
```


Confirm:


```
volume show -vserver <dr_svm> -volume <dr_volume> -fields type
```


Expected: RW

---

**Step 5 — Create or Validate Junction Path (NFS Only)**
--------------------------------------------------------

If the junction path does not yet exist:


```
volume mount -vserver <dr_svm> -volume <dr_volume> -junction-path /<junction_name>
```


---

**Step 6 — Create SMB Shares (SMB Workloads Only)**
---------------------------------------------------

Recreate shares using ONTAP CLI:


```
vserver cifs share create \
  -vserver <dr_svm> \
  -share-name <sharename> \
  -path /<junction_name>
```


Validate:


```
vserver cifs share show -vserver <dr_svm>
```


---

**Step 7 — Update DNS or Application Mount Targets**
----------------------------------------------------

Redirect clients to DR:

### **SMB Example**


```
\\<dr-cifs-endpoint>\<share>
```


### **NFS Example**


```
mount <dr-nfs-endpoint>:/<junction_name> /mnt/<mountpoint>
```


---

**Step 8 — Validate Access**
----------------------------

Confirm from an EC2 instance in DR that:

* Mounts succeed
* Permission model matches expectations
* SMB authentication works
* Applications read/write successfully

Failover is now complete.

---

**4. Operating in DR Mode**
===========================

While running in DR:

* DR filesystem hosts active read/write workloads
* SnapMirror relationship remains broken
* Primary region is not receiving updates until failback preparation begins

---

**5. Failback Procedure**
=========================

*DR Region → Primary Region*

Failback reestablishes the primary region as the authoritative copy.

---

**Step 1 — Validate Primary Filesystem Availability**
-----------------------------------------------------

Confirm:

* Primary filesystem is **Available**
* SVM is reachable
* Routing to AD and EC2 clients is functioning

---

**Step 2 — Reverse Synchronization (Resync)**
---------------------------------------------

This establishes a new SnapMirror relationship from DR → primary.


```
snapmirror resync \
  -source-path <dr_svm>:<dr_volume> \
  -destination-path <primary_svm>:<primary_volume>
```


Check progress:


```
snapmirror show -destination-path <primary_svm>:<primary_volume>
```


Proceed only after lag reaches **0**.

---

**Step 3 — Quiesce and Break the DR → Primary Mirror**
------------------------------------------------------


```
snapmirror quiesce -destination-path <primary_svm>:<primary_volume>
snapmirror break  -destination-path <primary_svm>:<primary_volume>
```


Primary volumes are now writeable.

---

**Step 4 — Reapply Junction Path (NFS) or SMB Shares**
------------------------------------------------------

Use the same procedure as initial setup:

### **NFS Junction Path**


```
volume mount -vserver <primary_svm> \
  -volume <primary_volume> \
  -junction-path /<junction_name>
```


### **SMB Share Recreation**


```
vserver cifs share create \
  -vserver <primary_svm> \
  -share-name <sharename> \
  -path /<junction_name>
```


---

**Step 5 — Redirect Workloads Back to Primary**
-----------------------------------------------

Update DNS, UNC paths, or mount commands accordingly.

Validate access from EC2 instances.

---

**Step 6 — Re-Establish Normal SnapMirror**
-------------------------------------------

Once workloads are fully back on primary:


```
snapmirror create \
  -source-path <primary_svm>:<primary_volume> \
  -destination-path <dr_svm>:<dr_volume>

snapmirror initialize -destination-path <dr_svm>:<dr_volume>
```


This restores the normal Primary → DR replication direction.

---

**6. Command Reference Summary**
================================

### **SnapMirror**


```
snapmirror update
snapmirror show
snapmirror quiesce
snapmirror break
snapmirror resync
snapmirror initialize
```


### **Volume Operations**


```
volume mount
volume show
volume modify
```


### **SMB**


```
vserver cifs share create
vserver cifs share show
```


### **NFS Export Policy (If Required)**


```
vserver export-policy rule create
vserver export-policy show
```


---

**7. Notes for Implementation**
===============================

* All DR filesystem, SVM, and volume definitions should continue to be created and modified via CDK for consistency and compliance with the existing platform model.
* Share creation and SnapMirror manipulation continue to be performed through ONTAP CLI on the management endpoint.
* AD integration steps for the DR SVM follow the same process used for the primary SVM. *(Optional link — INSERT LINK)*