# Decision---IDS-and-IPS-Design

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098009/Decision---IDS-and-IPS-Design

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Kyle Pearson (Deactivated) on July 28, 2025 at 08:57 PM

---

### Document Lifecycle Status

**Purpose**
-----------

This document outlines a strategy for providing IDS/IPS protection for applications running in AWS.

### Decision

Determine usage of IDS/IPS protection

### **Host-based IDS/IPS protection**

Host-based IDS/IPS protection provides the following general capabilities and benefits:

1. Acts as an additional layer of security for Layer3/Layer4 traffic by scanning and analyzing suspicious content for potential threats.
2. When placed in the direct communication path, an IPS takes automatic action on suspicious traffic within the network.
3. Automatically scales protection with the load.
4. Uses additional context available on the host for anomaly detection.
5. Simplifies network design and operations.

You can also utilize IDS/IPS capabilities in routing, through either native AWS Network Firewall or forcing traffic to an Amazon Gateway Load Balancer for a 3rd party appliance. Some of the benefits are:

1. Deep packet inspection
2. Use custom lists of known bad domains to limit outbound traffic from network
3. Filtering to known endpoints (service domains, IP address endpoints)
4. Use of stateful protocol detections
5. Enforcing a combination of inspection techniques at scale (east-west, north-south) for environment.

### **Example Decisions**

* Host-based IDS/IPS will be installed on all hosts to provide for IDS/IPS protection.
* Amazon Network Firewall Endpoints for ingress application traffic to perform deep packet inspection.

### **Customer Specific IDS/IPS Decisions**

**Decision**

Document the IDS/IPS protection requirements that are to be implemented

1. AWS Firewall Manager to be used for centralized management
2. Network-based IPS must be implemented for North/South traffic
3. Network-based IPS must be implemented for East/West traffic, but may start as IDS
4. AWS Network Firewall must perform Deep Packet Inspection