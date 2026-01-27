# DACI: Four Region AWS Infrastructure Strategy

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4989812796/DACI%3A%20Four%20Region%20AWS%20Infrastructure%20Strategy

**Created by:** Kaitlin Wieand on August 06, 2025  
**Last modified by:** Kaitlin Wieand on August 06, 2025 at 01:42 PM

---

Decision
--------

**Should we expand our AWS infrastructure to four regions (us-east-1, us-east-2, us-west-1, us-west-2) to support HRP's performance requirements and future growth?**

Background
----------

* HRP currently uses two datacenters (MA/OH) but requires better west coast performance
* HRP needs primary and DR region selection based on customer proximity
* Previous recommendation for four-datacenter approach was not implemented
* West coast customers experiencing suboptimal performance with current setup

---

DACI Framework
--------------

### **D - Driver**

**Infrastructure Architecture Lead**

* Owns final decision and accountability for outcome
* Responsible for implementation timeline and resource allocation
* Will communicate decision and rationale to organization

### **A - Approver**

**Enterprise Architect & CTO**

* Must approve budget and resource allocation
* Signs off on infrastructure strategy alignment
* Has veto power on final recommendation

### **C - Contributors**

* **HRP Product Lead**: Customer requirements and performance SLAs
* **Site Reliability Engineering**: Operational complexity and monitoring
* **Security Team**: Compliance and data residency requirements
* **Finance**: Cost modeling and budget impact analysis
* **Cloud Infrastructure Team**: Technical implementation and migration planning

### **I - Informed**

* Engineering leadership team
* HRP engineering teams
* Other product teams that may benefit
* Customer success teams
* Executive leadership

---

Tenet-Based Analysis
--------------------

### **Tenet 1: Customer Experience First**

* ✅ **Supports**: Dramatically improves west coast latency and performance
* ✅ **Supports**: Enables optimal region selection for all customers
* **Weight**: High priority

### **Tenet 2: Operational Excellence**

* ⚠️ **Mixed**: Increases operational complexity with more regions to manage
* ✅ **Supports**: Provides better disaster recovery and resilience options
* **Weight**: Medium priority

### **Tenet 3: Cost Efficiency**

* ❌ **Conflicts**: Higher infrastructure costs across four regions
* ✅ **Supports**: May reduce over-provisioning by distributing load
* **Weight**: Medium priority

### **Tenet 4: Speed to Market**

* ❌ **Conflicts**: Significant implementation time and migration effort
* ✅ **Supports**: Future product launches can leverage optimal regions immediately
* **Weight**: Medium priority

### **Tenet 5: Data-Driven Decisions**

* ✅ **Supports**: Based on measurable customer performance requirements
* ✅ **Supports**: Anshul's analysis shows clear west coast performance gaps
* **Weight**: High priority

---

Recommendation
--------------

**Proceed with four-region expansion** based on tenet analysis:

### **Why This Aligns with Our Tenets:**

1. **Customer Experience First** strongly supports this decision
2. **Data-Driven Decisions** validates the need through performance analysis
3. Operational complexity is manageable with proper planning
4. Cost increase is justified by customer value and competitive positioning

### **Implementation Approach:**

* **Phase 1**: Deploy us-west-2 for immediate west coast improvement
* **Phase 2**: Add us-west-1 for full regional coverage and redundancy
* **Timeline**: 6-month phased rollout to minimize risk

### **Success Metrics:**

* West coast latency improvement: <100ms target
* Customer satisfaction scores in western regions
* System availability and DR capabilities
* Total cost of ownership vs. performance gains