# FSx for NetApp ONTAP – Disaster Recovery Assessment

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5306581074/FSx%20for%20NetApp%20ONTAP%20%E2%80%93%20Disaster%20Recovery%20Assessment

**Created by:** Alex Dixon on December 04, 2025  
**Last modified by:** Alex Dixon on December 09, 2025 at 02:09 PM

---

**1. Purpose**
--------------

This document describes the recommended disaster recovery (DR) architecture for the customer’s Amazon FSx for NetApp ONTAP (FSxN) environment. It defines the cross-region deployment approach, replication configuration, and operational steps required to achieve the following recovery objectives:

* **Recovery Time Objective (RTO):** 4 hours
* **Recovery Point Objective (RPO):** 30 minutes

The design aligns fully with the existing FSxN implementation patterns documented in the customer’s internal guide, including CDK-driven infrastructure deployment, Active Directory integration for SVMs, SMB/CIFS share creation using ONTAP CLI, and DataSync migration patterns.

---

**2. Current Architecture From** Guiding Care: FSx NetApp ONTAP Implementation Guide
------------------------------------------------------------------------------------

![GC-Shared-Storage-TA.drawio_(1).png](images/GC-Shared-Storage-TA.drawio_(1).png)

---

**3. Disaster Recovery Architecture**
-------------------------------------

### **3.1 DR FSxN Deployment (CDK-Defined)**

The recommended DR deployment is a **Single-AZ FSx for ONTAP filesystem**, created using the same CDK structure already used for the primary environment.

A Single-AZ filesystem is appropriate because:

* It meets the 4-hour RTO
* It avoids unnecessary Multi-AZ cost in DR
* SnapMirror promotion and share creation fall well within the allowable recovery window

### **DR Filesystem (CDK Example)**


```
- id: dr-fsx
  name: "gc-fsxn-shared-dr"
  preferred_subnet_id: "<dr-private-subnet>"
  <<: *fsx_template
  deployment_type: "SINGLE_AZ_1"
  tags:
    <<: *common_tags
    ResourceType: "FSxFileSystem"
```


### **DR SVM (AD-Integrated)**


```
svms:
  - id: smb-svm-dr
    name: "gc-svm-dr-use2"
    filesystem_id: "dr-fsx"
    <<: *svm_ad_template
```


This mirrors the AD-integration behavior described in the existing guide.

### **DR Volumes (SnapMirror Targets)**


```
volumes:
  - id: GC-Share-DR
    name: "GC_SHARE_DR"
    svm_id: "smb-svm-dr"
    junction_path: "/GC-SHARE-DR"
    <<: *volume_template
```


---

**4. Cross-Region Replication Strategy**
----------------------------------------

### **4.1 SnapMirror Replication — Full Setup Procedure**

### **Prerequisites**

* DR filesystem, SVM, and volumes exist (via CDK?)
* Cluster peering ports (11104–11105/TCP) allowed between regions
* SnapMirror port (10000/TCP) allowed between regions
* DNS resolution and AD reachability validated if using SMB

**Step 1 — Establish Cluster Peering**
--------------------------------------

Run on **each** cluster:


```
cluster peer create \
  -address-family ipv4 \
  -peer-addrs <intercluster_lif_ip_of_other_region> \
  -passphrase <shared_secret>
```


Confirm peering:


```
cluster peer show
```


---

**Step 2 — Establish SVM Peering**
----------------------------------

On the **destination (DR)** cluster:


```
vserver peer create \
  -vserver <dr_svm> \
  -peer-vserver <primary_svm> \
  -applications snapmirror
```


Check status:


```
vserver peer show
```


---

**Step 3 — Create Destination Volume (CDK-Provided)**
-----------------------------------------------------

*No CLI action required* if CDK is already creating DR volumes using the shared volume\_template.

To verify the DR volume exists:


```
volume show -vserver <dr_svm>
```


---

**Step 4 — Create SnapMirror Relationship**
-------------------------------------------

On the **DR** SVM:


```
snapmirror create \
  -source-path <primary_svm>:<primary_volume> \
  -destination-path <dr_svm>:<dr_volume> \
  -type XDP
```


---

**Step 5 — Initialize Replication**
-----------------------------------

Initial baseline transfer:


```
snapmirror initialize \
  -destination-path <dr_svm>:<dr_volume>
```


Monitor progress:


```
snapmirror show -destination-path <dr_svm>:<dr_volume> \
  -fields last-transfer-size,last-transfer-end-timestamp,lag-time
```


---

**Step 6 — Configure Replication Schedule**
-------------------------------------------

Example 30-minute RPO schedule:


```
snapmirror modify \
  -destination-path <dr_svm>:<dr_volume> \
  -schedule "15min"   # or create a custom 30 min schedule
```


To use a custom 30-minute schedule:


```
job schedule cron create \
  -name "every30min" \
  -minute "0,30"

snapmirror modify \
  -destination-path <dr_svm>:<dr_volume> \
  -schedule "every30min"
```


---

**Step 7 — Verify SnapMirror Relationship**
-------------------------------------------


```
snapmirror show \
  -destination-path <dr_svm>:<dr_volume>
```


Expected state after initialization: Snapmirrored

---

**Step 8 — Ongoing Validation**
-------------------------------

Validate periodically that:

* SnapMirror transfers succeed
* Lag time remains within RPO target
* DR volumes are present and reachable

### **4.2 Replication Schedule**

A **30-minute SnapMirror schedule** is recommended to meet the defined RPO. This can be reduced to 5 minutes to accommodate lower RPO in the future.

### **4.3 Network & Security Requirements**

SnapMirror requires:

| **Ports** | **Purpose** |
| --- | --- |
| TCP 11104–11105 | Cluster peering |
| TCP 10000 | SnapMirror data transfer |
| AD & DNS ports | Required for SMB authentication |

These port requirements match the diagrams shown in the existing implementation guide.

AWS Transit Gateway provides the routing path required for inter-region communication between ONTAP intercluster endpoints.

---

**5. Active Directory Requirements in DR**
------------------------------------------

If SMB workloads are used, AD must be reachable and fully functional in the DR region.

Requirements:

* Domain controllers must exist in DR
* DNS servers must be reachable by the DR SVM
* DR SVM must be joined to AD using the same workflow used in primary

This ensures authentication continuity during failover.

---

**6. Failover Model (Primary → DR)**
------------------------------------

Failover activates the DR filesystem and makes shares accessible to workloads in the DR region.

### **High-Level Failover Sequence**

1. Suspend application writes (if possible)
2. Perform a final SnapMirror update
3. Quiesce the SnapMirror relationship
4. Break SnapMirror to promote DR volume to read/write
5. Ensure junction paths exist (NFS)
6. Recreate SMB shares on the DR SVM
7. Update DNS or application endpoints
8. Validate EC2 access to the DR shares

These steps reuse the same ONTAP CLI procedures already documented for primary SMB share creation.

---

**7. Failback Model (DR → Primary)**
------------------------------------

Failback restores operations to the primary region once available.

### **High-Level Failback Sequence**

1. Validate that the primary filesystem is online
2. Resync SnapMirror from DR → primary
3. Once synchronized, break SnapMirror on the primary
4. Recreate junction paths or SMB shares as required
5. Redirect clients back to primary
6. Re-establish normal SnapMirror from primary → DR

This workflow mirrors the initial SnapMirror setup and uses the same CLI patterns outlined in the user’s current documentation.

---

**8. DR Validation Expectations**
---------------------------------

To ensure operational readiness, the organization should periodically validate:

* That SnapMirror relationships can be successfully promoted
* That the DR SVM can authenticate against domain controllers
* That SMB shares on DR can be created and accessed
* That EC2 instances in DR can mount shares through TGW routing
* That CDK deployments for DR resources run without error

These validation steps follow the same pattern as existing DataSync testing and SMB share validation.

---

**9. Summary of Recommendations**
---------------------------------

### **Architecture**

* Deploy **Single-AZ FSxN** filesystem in DR
* Use CDK to define DR filesystem, SVM, and volumes
* Maintain consistency with existing primary-region configurations

### **Replication**

* Use SnapMirror for cross-region replication
* Configure a **30-minute interval** to meet RPO

### **Operations**

* Follow standardized failover and failback steps
* Reuse established ONTAP CLI patterns for SMB share creation
* Ensure AD infrastructure exists in DR to support SMB authentication

---