# Decision-AWS-Control-Tower-Launch-Parameters

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065008/Decision-AWS-Control-Tower-Launch-Parameters

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Gary Edwards on July 11, 2025 at 08:49 PM

---

**Purpose**
-----------

To document the parameter values that will be used when deploying AWS Control Tower.

Decision
--------

Determine AWS Control Tower parameter values

AWS Control Tower allows customers to specify an encryption key (backed by AWS KMS) to encrypt objects in the Amazon Simple Storage Service (Amazon S3) configuration bucket, Amazon SQS queue, as well as parameters stores in Systems Manager Parameter Store. If enabled, customers can select a pre-existing key or create a new KMS key for encrypting objects at rest.

**AWS Control Tower setup and parameters**
------------------------------------------



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table ac:local-id="88634473-ac49-450a-9eca-ccd96318f270" data-layout="default" data-table-width="1800"><tbody><tr><th>Section</th><th>Parameter Name</th><th>Parameter Value</th></tr><tr><th>Control Tower Home Region</th><td>Region</td><td>us-east-1</td></tr><tr><th>Additional Control Tower Regions</th><td>Additional Region(s) (<em>Optional)</em>
</td><td>us-west-2</td></tr><tr><th>Control Tower Foundational OU</th><td>Foundational OU</td><td>Security</td></tr><tr><th>Control Tower Additional OU</th><td>Additional OU (<em>Optional)</em>
</td><td>Infrastructure</td></tr><tr><th>Control Tower KMS Key</th><td>KMS Encryption (KMS Customer key is created during the AWS Control Tower deployment)</td><td>Enable
<br/>
</td></tr><tr><th rowspan="3">Core Account Email Addresses</th><th>Root Account Email Address</th><th><a href="mailto:aws@healthedge.com">aws@healthedge.com</a></th></tr><tr><td>LogArchive Account Email Address</td><td><a href="mailto:aws+log-archive@healthedge.com">aws+log-archive@healthedge.com</a></td></tr><tr><td>Audit Account Email Address</td><td><a href="mailto:aws+audit@healthedge.com">aws+audit@healthedge.com</a>
</td></tr></tbody></table>

