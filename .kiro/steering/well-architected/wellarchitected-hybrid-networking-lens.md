---
inclusion: manual
---

# AWS Well-Architected Framework - Hybrid Networking Lens

## Document Overview

Best practices for designing and operating reliable, secure, efficient, and cost-effective hybrid networking systems connecting AWS and on-premises environments.

## Hybrid Networking Components

- **AWS Site-to-Site VPN**: IPsec tunnels over internet
- **AWS Direct Connect**: Dedicated physical connection to AWS
- **AWS Transit Gateway**: Central hub for VPC and on-premises connectivity
- **Virtual Private Gateway**: VPN termination for single VPC

## Operational Excellence

### IP Address Allocation
- Implement well-defined IP address allocation scheme
- Avoid overlapping CIDR ranges between VPC and on-premises
- Track IP prefixes and allocate CIDR ranges systematically
- Right-size CIDR ranges for VPCs based on workload requirements

### Health Monitoring
- Use CloudWatch to collect metrics from Direct Connect and VPN
- Leverage Transit Gateway statistics and logs
- Use Transit Gateway Network Manager for global network view

### Operational Event Management
- Use AWS Health Dashboard for maintenance notifications
- Prepare for unplanned outages with redundant connections
- Enable Bidirectional Forwarding Detection (BFD) for fast failover
- Test high-availability design periodically

## Security

### Identity and Access Management
- Implement landing zone with AWS Control Tower
- Create separate Central Networking account
- Apply principle of least privilege for network resources
- Tag AWS hybrid network resources upon creation

### Network Segmentation
- Verify customer gateway configurations align with traffic separation
- Control access between on-premises and AWS environments
- Use role-based access control for AWS platform access

### Infrastructure Protection
- Use security groups as stateful (layer 4) firewalls
- Implement Network ACLs as stateless firewalls
- Configure Transit Gateway route tables for defined connectivity
- Deploy AWS Network Firewall for Direct Connect and VPN traffic
- Use Route 53 Resolver DNS Firewall for DNS-level protection

### Data Protection
- Use IPSec VPN for encrypted tunnels over internet
- Configure MACsec encryption for dedicated 10Gbps+ Direct Connect
- Use application-level encryption for hosted connections
- Leverage certificates for authentication

## Reliability

### Service Quotas
- Monitor and adjust service quotas for business needs
- Proactively manage quotas using CloudWatch alarms
- Ensure sufficient gap between quotas and maximum usage

### Change Management
- Prepare for AWS Direct Connect scheduled maintenance
- Consider redundant Direct Connect or VPN backups
- Monitor bandwidth usage and increase capacity as needed

### Failure Management
- Design highly resilient connections with redundancy
- Connect from multiple data centers for location redundancy
- Use redundant hardware and telecommunications providers
- Configure both tunnels for VPN connections
- Test failover scenarios regularly

## Performance Efficiency

### Connectivity Selection
- Choose between Direct Connect and VPN based on bandwidth, latency, jitter
- Select right VPN termination endpoint
- Consider accelerated Site-to-Site VPN for better performance

### Direct Connect Implementation
- Choose locations that minimize combined latency
- Select right termination endpoint (private or transit virtual interface)
- Consider AWS Local Zones for very low latency
- Use Link Aggregation Groups (LAG) for multiple connections

### Monitoring and Scaling
- Track usage of VPN and Direct Connect using CloudWatch
- Estimate bandwidth requirements for new applications
- Scale VPN bandwidth using Transit Gateway and ECMP
- Add Direct Connect capacity through LAG or additional connections

## Cost Optimization

### Usage Monitoring
- Integrate network monitoring with cloud monitoring
- Use AWS Cost & Usage Report and VPC Flow Logs
- Leverage Athena and QuickSight for cost analysis

### Cost-Effective Selection
- Use internet-based VPN for non-mission critical workloads
- Start with internet-based connections during testing
- Use Virtual Private Gateway for small hybrid setups
- Use Transit Gateway for multiple VPCs

### Data Transfer Optimization
- Understand data transfer costs for different options
- Consider Direct Connect for high-volume data transfer
- Be aware of Transit Gateway data processing costs
- Choose termination option based on data transfer patterns

## DR-Specific Networking Considerations

### Disaster Recovery Connectivity
- Implement redundant network paths for DR traffic
- Use Direct Connect with VPN backup for critical DR workloads
- Configure appropriate bandwidth for replication traffic
- Monitor replication lag related to network performance

### Cross-Region DR
- Use Transit Gateway peering for cross-region connectivity
- Consider data transfer costs in DR architecture
- Implement proper routing for failover scenarios
- Test network failover as part of DR drills

## Key Concepts

### Direct Connect Components
- **Dedicated Connection**: Physical Ethernet (1, 10, 100 Gbps)
- **Hosted Connection**: Via AWS Partners (50 Mbps to 10 Gbps)
- **Virtual Interfaces**: Logical connections (public, private, transit)

### Transit Gateway
- Fully managed cloud router
- Connects VPCs and on-premises through central hub
- Supports ECMP routing for load balancing
- Enables rich routing scenarios

### Link Aggregation Group (LAG)
- Aggregates multiple connections at single Direct Connect location
- Treated as single managed connection
- Limited to two 100G or four connections under 100G
