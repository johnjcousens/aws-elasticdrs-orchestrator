# Server Preparation - Rehost GC Server Scope

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5428379685/Server%20Preparation%20-%20Rehost%20GC%20Server%20Scope

**Created by:** Lei Shi on January 08, 2026  
**Last modified by:** Lei Shi on January 08, 2026 at 08:25 PM

---

Windows
-------

### ***OS Firewall Readiness (if enabled):***

* Inbound allow on port TCP-3389/5985/5986 from source of AWS CIDR Blocks. (If no specific rules configured yet, you can set two range of 10.192.0.0/10 and 192.168.0.0/16)
* Outbound allow on port TCP/UDP-53 to destination of "10.199.29.107, 10.199.30.118,10.199.31.54" for IAD3 servers, and "10.223.13.68,10.223.14.220,10.223.15.172" for LAX3 servers
* Outbound allow on port TCP-443 to destination of 10.192.0.0/10

### ***Credential Privilege readiness:*** `altruista\awsmgnsvc`

* Allow execute command of “`ipconfig *`” and “`wmic diskdrive list brief`”
* Allow execute command of “`tnc s3.<aws-region>.amazonaws.com -port 443`” and “`tnc mgn.<aws-region>.amazonaws.com -port 443`”
* Allow download MGN agent installer
* Allow install MGN agent

### ***SecureBoot is disabled***

### ***Check and notify AWS ProServ Team if the servers are set as UEFI boot***

### ***Windows GPO is either disabled or not blocking above activities***

### ***Make sure the source server never reboot after AWS MGN agent installation***

Linux
-----

### ***OS Firewall Readiness (if enabled):***

* Inbound allow on port TCP-3389/5985/5986 from source of AWS CIDR Blocks. (If no specific rules configured yet, you can set two range of 10.192.0.0/10 and 192.168.0.0/16)
* Outbound allow on port TCP/UDP-53 to destination of "10.199.29.107, 10.199.30.118,10.199.31.54" for IAD3 servers, and "10.223.13.68,10.223.14.220,10.223.15.172" for LAX3 servers
* Outbound allow on port TCP-443 to destination of 10.192.0.0/10

### ***Credential Privilege readiness:*** `altruista\awsmgnsvc`

* Allow execute command of “`ipconfig *`” and “`wmic diskdrive list brief`”
* Allow execute command of “`curl -v telnet://s3.<aws-region>.amazonaws.com:443`” and “`curl -v telnet://mgn.<aws-region>.amazonaws.com:443`”
* Allow download MGN agent installer
* Allow install MGN agent

### ***SecureBoot is disabled***

### ***SELinux is disabled***

### ***Kernel/Header/Devel/MGN-requried-Package-per-OS-flavor is installed***

### ***Sudoers modified for awsmgnsvc user***

### ***Mount set for awsmgnsvc user***

### ***Any other Linux configuration if distro is unique***

### ***Check and notify AWS ProServ Team if the servers are set as UEFI boot***

### ***Some Linux configuration above reboot once/none matters, please make sure the Linux Server is fully prepared***

### ***Make sure the source server never reboot after AWS MGN agent installation***