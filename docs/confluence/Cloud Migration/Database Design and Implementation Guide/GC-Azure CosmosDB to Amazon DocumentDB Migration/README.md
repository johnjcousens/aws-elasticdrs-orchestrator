# GC-Azure CosmosDB to Amazon DocumentDB Migration

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5263098002/GC-Azure%20CosmosDB%20to%20Amazon%20DocumentDB%20Migration

**Created by:** Sateesh Bammidi on November 21, 2025  
**Last modified by:** Sateesh Bammidi on December 11, 2025 at 06:59 PM

---

**Azure Cosmos DB** is a globally distributed, multi-model database service that supports document, key-value, graph, and column-family data models with APIs for MongoDB, SQL, Cassandra, Gremlin, and Table storage, offering 99.999% availability SLA, five tunable consistency levels, automatic scaling, and serverless pricing options.

**Amazon DocumentDB** is a fully managed document database that's compatible with MongoDB 3.6/4.0/5.0/8.0 APIs, providing deep AWS ecosystem integration with VPC and IAM, automatic storage scaling up to 128 TB with 6-way replication, up to 15 read replicas for microsecond read latency, continuous backup with 35-day point-in-time recovery, and built-in encryption.

There are different ways to migrate data from Document store to Amazon DocumentDB as listed below. But this post elaborates about MongoDump/MongoRestore way to migrate from Azure CosmosDB to Amazon DocumentDB for GuidingCare.

* AWS Database Migration Service (DMS) - offline, Online, Hybrid - This approach is suitable if we are looking for little to no downtime
* MongoDump/MongoRestore - This approach is suitable if we can afford some downtime. In our case we have 4 hrs RTO and 30 mins RPO.

Below is architecture diagram of mongodumo/mongorestore process:

![image-20251121-180150.png](images/image-20251121-180150.png)

Listed below are the steps to perform mongodump/mongorestore:

High level steps to migrate Data
--------------------------------

Here are the high level steps involved in mongodump/mongorestore

1. Verify your source version(compatible) and configuration
2. Set up and choose the size of your Amazon Document DB cluster
3. Set up an EC2 instance
4. Connect to Azure CosmosDb and Amazon DocumentDB
5. Perform to mongodump on Azure CosmosDb and mongorestore on Amazon DocumentDB

### Verifying your source version and configuration

If your MongoDB source uses a version of MongoDB earlier than 3.6, you should upgrade your source deployment and your application drivers. They should be compatible with MongoDB 3.6 to migrate to Amazon DocumentDB.You can determine the version of your source deployment by entering the following code in the mongo shell:


```
mongoToDocumentDBOnlineSet1:PRIMARY> db.version()
3.4.4
```


Also, verify that the source MongoDB cluster (or instance) is configured as a replica set. You can determine if a MongoDB cluster is configured as a replica set with the following code:


```
db.adminCommand( { replSetGetStatus : 1 } )
```


If the output is an error message similar to “”errmsg” : “not running with –replSet””, the cluster is not configured as a replica set.

### Setting up and sizing your source Amazon DocumentDB cluster

For this post, your target Amazon DocumentDB cluster is a replica set that you create with a single db.t4g.medium instance. When you size your cluster, choose the instance type that is suitable for your production cluster. For more information about Amazon DocumentDB instances and costs, see [Amazon DocumentDB (with MongoDB compatibility) pricing](https://aws.amazon.com/documentdb/pricing/).

### Setting up an EC2 instance

To connect to the Amazon DocumentDB cluster to migrate indexes and for other tasks during the migration, create an EC2 instance in the same VPC as your cluster and install the mongo shell. Ensure you have a EBS volume with enough capacity to hold the backup files. For instructions, see [Getting Started with Amazon DocumentDB](https://docs.aws.amazon.com/documentdb/latest/developerguide/getting-started.html). To verify the connection to Amazon DocumentDB, enter the following CLI command:

Please use default Amazon Linux 2023 during the Amazon EC2 configuration, enter this command upon logging in:

1. Create the repository file. At the command line of your EC2 instance you created, execute the follow command:  
   `echo -e "[mongodb-org-5.0] \nname=MongoDB Repository\nbaseurl=https://repo.mongodb.org/yum/amazon/2023/mongodb-org/5.0/x86_64/\ngpgcheck=1 \nenabled=1 \ngpgkey=https://pgp.mongodb.com/server-5.0.asc" | sudo tee /etc/yum.repos.d/mongodb-org-5.0.repo`
2. When it is complete, install mongosh with one of the two following command options at the command prompt:

`sudo yum install -y mongodb-mongosh-shared-openssl3`

3. When it is complete, install the mongodb 5.0 shell with the following command option at the command prompt:

`sudo yum install -y mongodb-org-shell`

4. Download the Amazon DocumentDB Certificate Authority (CA) certificate required to authenticate to your cluster:

`wget https://truststore.pki.rds.amazonaws.com/global/global-bundle.pem`

### Connect to Azure CosmosDb and Amazon DocumentDB

1. At this point you should be able to connect to Azure CosmosDB and Amazon DocumentDB

CosmosDB:  
`mongo --ssl --host <Host name>:<Port> --username <UserName> --password <Password>`

DocumentDB:  
`mongosh <Host name>:27017 --tls --tlsCAFile global-bundle.pem --retryWrites=false --username <UserName> --password <insertYourPassword>`

### Perform to mongodump on Azure CosmosDb and mongorestore on Amazon DocumentDB

1. Initiate Mongodump to a directory dump (in this example) for Azure CosmosDB  
     
   `mongodump "mongodb://testuser:testpwd@testmongo.cosmos.azure.com:10255/?ssl=true"`
2. Restore using mongorestore from the dump location in step-6 for the Amazon DcouemntDB

`mongorestore --uri="mongodb://testuser:testpwd@test.us-east-1.docdb.amazonaws.com:27017/?tls=true&tlsCAFile=global-bundle.pem&replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false" ./dump`

### Grant IAM role access to the DocumentDB


```
use $external;
db.createUser(
    {
        user: "arn:aws:iam::<AWS Account>:role/<IAM Role name>",
        mechanisms: ["MONGODB-AWS"],
        roles: [{role: "readWriteAnyDatabase", db: "admin"}]
    }
);
```


**References:**
---------------

* [https://docs.aws.amazon.com/documentdb/latest/developerguide/connect-ec2-manual.html#manual-connect-ec2.install-mongo-shell:~:text=If you are using IAM%2C you must use the previous version of the MongoDB shell (5.0) to connect to your Amazon DocumentDB cluster%2C follow these steps%3A](https://docs.aws.amazon.com/documentdb/latest/developerguide/connect-ec2-manual.html#manual-connect-ec2.install-mongo-shell:~:text=If%20you%20are%20using%20IAM%2C%20you%20must%20use%20the%20previous%20version%20of%20the%20MongoDB%20shell%20(5.0)%20to%20connect%20to%20your%20Amazon%20DocumentDB%20cluster%2C%20follow%20these%20steps%3A)
* <https://docs.aws.amazon.com/documentdb/latest/developerguide/docdb-migration-runbook.html>