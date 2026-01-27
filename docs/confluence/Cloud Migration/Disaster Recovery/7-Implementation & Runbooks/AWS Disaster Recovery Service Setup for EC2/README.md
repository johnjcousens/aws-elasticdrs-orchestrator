# AWS Disaster Recovery Service Setup for EC2

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5293703259/AWS%20Disaster%20Recovery%20Service%20Setup%20for%20EC2

**Created by:** Venkata Kommuri on December 02, 2025  
**Last modified by:** Venkata Kommuri on December 02, 2025 at 07:42 PM

---

AWS Elastic Disaster Recovery (DRS) for Cross-Region EC2
--------------------------------------------------------

**AWS Elastic Disaster Recovery** is the recommended service for protecting EC2 instances across regions. It continuously replicates your source servers to a recovery target in another AWS Region, enabling recovery with RPO (Recovery Point Objective) of seconds and RTO (Recovery Time Objective) of minutes.

Key Implementation Steps
------------------------

### 1. **Prerequisites and Setup**

* Initialize DRS in both source and recovery AWS Regions
* Configure network settings including staging and recovery subnets
* Set up proper IAM roles with policies like `AWSElasticDisasterRecoveryEc2InstancePolicy`

  + 
```
# Create IAM role for DRS agent
aws iam create-role \
    --role-name AWSElasticDisasterRecoveryAgentRole \
    --assume-role-policy-document '{
        "Version": "October 17, 2012",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "drs.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }'

# Attach managed policy
aws iam attach-role-policy \
    --role-name AWSElasticDisasterRecoveryAgentRole \
    --policy-arn arn:aws:iam::aws:policy/AWSElasticDisasterRecoveryAgentInstallationPolicy

# Create instance profile
aws iam create-instance-profile \
    --instance-profile-name AWSElasticDisasterRecoveryAgentProfile

# Add role to instance profile
aws iam add-role-to-instance-profile \
    --instance-profile-name AWSElasticDisasterRecoveryAgentProfile \
    --role-name AWSElasticDisasterRecoveryAgentRole
            
```

* Ensure outbound internet access or configure VPC endpoints for secure environments

### 2. **Replication Configuration**

* Install the AWS Replication Agent on your source EC2 instances

  + download and installed the agent


```
# SSH into EC2 instance
ssh -i ec2-key.pem ubuntu@<ec2-instance-ip>
# Download DRS agent installer
wget -O aws-replication-installer-init.py \
    https://aws-elastic-disaster-recovery-us-east-1.s3.us-east-1.amazonaws.com/latest/linux/aws-replication-installer-init.py
# Make executable
chmod +x aws-replication-installer-init.py
# Install DRS agent
sudo python3 aws-replication-installer-init.py \
    --region us-east-1 \
    --aws-access-key-id AKIAIOSFODNN7EXAMPLE \
    --aws-secret-access-key wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY \
    --no-prompt
# Verify agent installation
sudo systemctl status aws-replication-agent
# Check agent logs
sudo tail -f /var/log/aws-replication-agent/agent.log

```


#### ⚠️ Agent Installation Notes

Agent must be installed on running instance

Requires root/sudo access for installation

Agent automatically starts replication after installation

Initial replication may take several hours depending on data size

Monitor replication progress in DRS console

* Configure replication settings through the DRS console
* Monitor replication progress via the DRS dashboard
* Data is continuously replicated to a staging area in the target region

### 3. **Testing with Recovery Drill**

* DRS launches a conversion server in the staging subnet during drill
* Validate that recovered instances meet the RTO requirements
* Test without impacting production workloads

### 4. **Failover Process**

* Launch recovery instances in the target region during an actual disaster
* Redirect traffic to the new recovery instances (using Active Directory DNS service)
* Validate application functionality in the recovery region

### 5. **Failback Process**

* Start reversed replication from recovery region back to source region
* Launch failback instances in the original source region
* Redirect traffic back to the source region
* Protect new instances by enabling replication again