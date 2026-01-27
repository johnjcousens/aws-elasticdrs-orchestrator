# Runbook-Database-Assessment-using-AWS-SCT

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867065824/Runbook-Database-Assessment-using-AWS-SCT

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:50 AM

---

| GreenTemplate | Draft | In Review | Baseline |
| --- | --- | --- | --- |

Introduction
============

AWS Schema Conversion Tool (AWS SCT) is used to convert your existing database schema from one database engine to another. You can convert relational OLTP schema, or data warehouse schema. Your converted schema is suitable for an Amazon Relational Database Service (Amazon RDS) MySQL, MariaDB, Oracle, SQL Server, PostgreSQL DB, an Amazon Aurora DB cluster, or an Amazon Redshift cluster. The converted schema can also be used with a database on an Amazon EC2 instance or stored as data on an Amazon S3 bucket.

AWS SCT supports the following OLTP conversions.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="ak-renderer-tableHeader-sortable-column" colspan="1" rowspan="1">
Source database
</th>
<th class="ak-renderer-tableHeader-sortable-column" colspan="1" rowspan="1">
Target database on Amazon RDS
</th>
</tr>
<tr>
<td colspan="1" rowspan="1">
Microsoft SQL Server (version 2008 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Aurora with MySQL compatibility, Amazon Aurora with PostgreSQL
                    compatibility, MariaDB 10.2 and 10.3, Microsoft SQL Server, MySQL, PostgreSQL
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
MySQL (version 5.5 and later)
</td>
<td colspan="1" rowspan="1">
Aurora PostgreSQL, MySQL, PostgreSQL
You can migrate schema and data from MySQL to an Aurora MySQL DB cluster
                    without using AWS SCT. 
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Oracle (version 10.2 and later)
</td>
<td colspan="1" rowspan="1">
Aurora MySQL, Aurora PostgreSQL, MariaDB 10.2 and 10.3, MySQL, Oracle,
                    PostgreSQL
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
PostgreSQL (version 9.1 and later)
</td>
<td colspan="1" rowspan="1">
Aurora MySQL, MySQL, PostgreSQL, Aurora PostgreSQL
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
IBM Db2 LUW (versions 9.1, 9.5, 9.7, 10.5, and 11.1)
</td>
<td colspan="1" rowspan="1">
Aurora MySQL, MariaDB 10.2 and 10.3, MySQL, PostgreSQL, Aurora PostgreSQL
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Apache Cassandra (versions 2.0, 3.0, 3.1.1, and 3.11.2)
</td>
<td colspan="1" rowspan="1">
Amazon DynamoDB
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Sybase ASE (12.5, 15.0, 15.5, 15.7, and 16.0)
</td>
<td colspan="1" rowspan="1">
Aurora MySQL, Aurora PostgreSQL, MySQL, PostgreSQL
</td>
</tr>
</tbody>
</table>



AWS SCT supports the following data warehouse conversions.



> **Note:** This is a complex table with merged cells. For best viewing experience, see the [original Confluence page].

<table>

<tbody>
<tr>
<th class="ak-renderer-tableHeader-sortable-column" colspan="1" rowspan="1">
Source database
</th>
<th class="ak-renderer-tableHeader-sortable-column" colspan="1" rowspan="1">
Target database on Amazon Redshift
</th>
</tr>
<tr>
<td colspan="1" rowspan="1">
Greenplum Database (version 4.3 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Microsoft SQL Server (version 2008 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Netezza (version 7.0.3 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Oracle (version 10 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Teradata (version 13 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
<tr>
<td colspan="1" rowspan="1">
Vertica (version 7.2.2 and later)
</td>
<td colspan="1" rowspan="1">
Amazon Redshift
</td>
</tr>
</tbody>
</table>



Using the multi-server assessor to create an aggregate report
=============================================================

To help determine the best target direction for your environment, you can use the multi-server assessor.

The *multi-server assessor* evaluates multiple servers based on input that you provide for each schema definition that you want to assess. Your schema definition contains database server connection parameters and the full name of each schema. After assessing each schema, the assessor produces a summary aggregated report that shows the estimated complexity for each possible migration target.

High Level Approach
===================

1. Identify a desktop/server in house having access to the entire data estate ( including all Oracle, MS SQL Server, MariaDB instances ) and install SCT on it. Refer the following link for installation instructions and media [https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP\_Installing.html](https://mcas-proxyweb.mcas.ms/certificate-checker?login=false&originalUrl=https%3A%2F%2Fdocs.aws.amazon.com.mcas.ms%2FSchemaConversionTool%2Flatest%2Fuserguide%2FCHAP_Installing.html "https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP_Installing.html")
2. Use an existing database account or create a dedicated account with the the following privileges to access the source database from SCT

   1. **Oracle** : The privileges required for Oracle as a source are listed following:

      * CONNECT
      * SELECT\_CATALOG\_ROLE
      * SELECT ANY DICTIONARY
      * SELECT on SYS.USER$ TO <sct\_user>
   2. **Microsoft SQL Server**: The privileges required for Microsoft SQL Server as a source are listed following:

      * VIEW DEFINITION
      * VIEW DATABASE STATE

      Repeat the grant for each database whose schema you are converting.
   3. **MariaDB:** The privileges required for MySQL as a source are listed following:

      * SELECT ON \*.\*
      * SELECT ON mysql.proc
      * SHOW VIEW ON \*.\*
3. Create a single CSV file having the following attributes for all the database schemas to be assessed.

![image2021-3-9_13-41-33.png](images/image2021-3-9_13-41-33.png)

```
The CSV file to be prepared for an assessment contains a column called Target Engines. To enter one or more AWS database targets, use the Target Engines column. Separate multiple target engines by using semicolons like this, MYSQL;MARIA\_DB. The number of targets affects the time it takes to run the assessment.
```

1. Performing a multi-server assessment. The procedure mentioned in the following link can be used to perform a multi server assessment with AWS SCT [https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP\_AssessmentReport.Multiserver.html](https://mcas-proxyweb.mcas.ms/certificate-checker?login=false&originalUrl=https%3A%2F%2Fdocs.aws.amazon.com.mcas.ms%2FSchemaConversionTool%2Flatest%2Fuserguide%2FCHAP_AssessmentReport.Multiserver.html "https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP_AssessmentReport.Multiserver.html")

**Note:** Databases can be grouped in multiple batches by creating multiple CSV files. Each CSV file would require a separate run and it would produce separate reports for each run.

References
==========

[https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP\_Welcome.html](https://mcas-proxyweb.mcas.ms/certificate-checker?login=false&originalUrl=https%3A%2F%2Fdocs.aws.amazon.com.mcas.ms%2FSchemaConversionTool%2Flatest%2Fuserguide%2FCHAP_Welcome.html "https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP_Welcome.html")

[https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP\_BestPractices.html](https://mcas-proxyweb.mcas.ms/certificate-checker?login=false&originalUrl=https%3A%2F%2Fdocs.aws.amazon.com.mcas.ms%2FSchemaConversionTool%2Flatest%2Fuserguide%2FCHAP_BestPractices.html "https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP_BestPractices.html")

[https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP\_Troubleshooting.html](https://mcas-proxyweb.mcas.ms/certificate-checker?login=false&originalUrl=https%3A%2F%2Fdocs.aws.amazon.com.mcas.ms%2FSchemaConversionTool%2Flatest%2Fuserguide%2FCHAP_Troubleshooting.html "https://docs.aws.amazon.com/SchemaConversionTool/latest/userguide/CHAP_Troubleshooting.html")

**Attachments:**

[image2021-3-9\_13-41-33.png](../../attachments/image2021-3-9_13-41-33.png)