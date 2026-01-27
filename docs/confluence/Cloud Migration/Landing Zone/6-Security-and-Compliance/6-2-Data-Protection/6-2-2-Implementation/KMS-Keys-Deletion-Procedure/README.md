# KMS-Keys-Deletion-Procedure

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867000189/KMS-Keys-Deletion-Procedure

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:34 AM

---

**Purpose**
-----------

Deleting an AWS KMS key (KMS key) from AWS Key Management Service (AWS KMS) is destructive and potentially dangerous. It deletes the key material and all metadata associated with the KMS key and is irreversible. After a KMS key is deleted, you can no longer decrypt the data that was encrypted under that KMS key, which means that data becomes unrecoverable. You should delete a KMS key only when you are sure that you don't need to use it anymore. If you are not sure, consider [disabling the KMS key](https://docs.aws.amazon.com/kms/latest/developerguide/enabling-keys.html) instead of deleting it. You can re-enable a disabled KMS key if you need to use it again later, but you cannot recover a deleted KMS key.

Before deleting a KMS key, you might want to know how many ciphertexts were encrypted under that KMS key. AWS KMS does not store this information and does not store any of the ciphertexts. To get this information, you must determine past usage of a KMS key. For help, go to [Determining past usage of a KMS key](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys-determining-usage.html).

AWS KMS never deletes your KMS keys unless you explicitly schedule them for deletion and the mandatory waiting period expires.

However, you might choose to delete a KMS key for one or more of the following reasons:

* To complete the key lifecycle for KMS keys that you no longer need
* To avoid the management overhead and [costs](https://aws.amazon.com/kms/pricing/) associated with maintaining unused KMS keys
* To reduce the number of KMS keys that count against your [KMS key resource quota](https://docs.aws.amazon.com/kms/latest/developerguide/resource-limits.html#kms-keys-limit)

If you [close or delete your AWS account](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/close-account.html), your KMS keys become inaccessible and you are no longer billed for them. You do not need to schedule deletion of your KMS keys separate from closing the account.

AWS KMS records an entry in your AWS CloudTrail log when you [schedule deletion](https://docs.aws.amazon.com/kms/latest/developerguide/ct-schedule-key-deletion.html) of the KMS key and when the [KMS key is actually deleted](https://docs.aws.amazon.com/kms/latest/developerguide/ct-delete-key.html).

**Procedure**
-------------

1. Assess key past usage:

   1. examine key permissions to determine scope of the potential usage;
   2. examine CloudTrail logs for the actual usage.
2. Disable key and actively monitor the usage:

   1. look for application errors;
   2. examine CloudTrail logs for failed API calls.
3. Schedule key for deletion and actively monitor the usage:

   1. set a waiting period appropriate for the key (7 to 30 days);
   2. set a CloudWatch Alarm to catch failed API calls against the key;
   3. if no key usage attempts were observed, no further action is required; otherwise, cancel key deletion before the waiting period ends.

**About the waiting period**
----------------------------

Because it is destructive and potentially dangerous to delete a KMS key, AWS KMS requires you to set a waiting period of 7 – 30 days. The default waiting period is 30 days.

However, the actual waiting period might be up to 24 hours longer than the one you scheduled. To get the actual date and time when the KMS key will be deleted, use the [DescribeKey](https://docs.aws.amazon.com/kms/latest/APIReference/API_DescribeKey.html) operation. Or in the AWS KMS console, on [detail page](https://docs.aws.amazon.com/kms/latest/developerguide/viewing-keys-console.html#viewing-details-navigate) for the KMS key, in the **General configuration** section, see the **Scheduled deletion date**. Be sure to note the time zone.

During the waiting period, the KMS key status and key state is **Pending deletion**.

* A KMS key pending deletion cannot be used in any [cryptographic operations](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#cryptographic-operations).
* AWS KMS does not [rotate the key material](https://docs.aws.amazon.com/kms/latest/developerguide/rotate-keys.html#rotate-keys-how-it-works) of KMS keys that are pending deletion.

After the waiting period ends, AWS KMS deletes the KMS key, its aliases, and all related AWS KMS metadata.

Use the waiting period to ensure that you don't need the KMS key now or in the future. You can [configure an Amazon CloudWatch alarm](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys-creating-cloudwatch-alarm.html) to warn you if a person or application attempts to use the KMS key during the waiting period. To recover the KMS key, you can cancel key deletion before the waiting period ends. After the waiting period ends you cannot cancel key deletion, and AWS KMS deletes the KMS key.

**Deleting asymmetric KMS keys**
--------------------------------

Users [who are authorized](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html#deleting-keys-adding-permission) can delete symmetric or asymmetric KMS keys. The procedure to schedule the deletion of these KMS keys is the same for both types of keys. However, because the [public key of an asymmetric KMS key can be downloaded](https://docs.aws.amazon.com/kms/latest/developerguide/download-public-key.html) and used outside of AWS KMS, the operation poses significant additional risks, especially for asymmetric KMS keys used for encryption (the key usage is `ENCRYPT_DECRYPT`).

* When you schedule the deletion of a KMS key, the key state of KMS key changes to **Pending deletion**, and the KMS key cannot be used in [cryptographic operations](https://docs.aws.amazon.com/kms/latest/developerguide/concepts.html#cryptographic-operations). However, scheduling deletion has no effect on public keys outside of AWS KMS. Users who have the public key can continue to use them to encrypt messages. They do not receive any notification that the key state is changed. Unless the deletion is canceled, ciphertext created with the public key cannot be decrypted.
* Alarms, logs, and other strategies that detect attempted use of KMS key that is pending deletion cannot detect use of the public key outside of AWS KMS.
* When the KMS key is deleted, all AWS KMS actions involving that KMS key fail. However, users who have the public key can continue to use them to encrypt messages. These ciphertexts cannot be decrypted.

If you must delete an asymmetric KMS key with a key usage of `ENCRYPT_DECRYPT`, use your CloudTrail Log entries to determine whether the public key has been downloaded and shared. If it has, verify that the public key is not being used outside of AWS KMS. Then, consider [disabling the KMS key](https://docs.aws.amazon.com/kms/latest/developerguide/enabling-keys.html) instead of deleting it.

**Deleting multi-Region keys**
------------------------------

Users [who are authorized](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html#deleting-keys-adding-permission) can schedule the deletion of multi-Region primary and replica keys. However, AWS KMS will not delete a multi-Region primary key that has replica keys. Also, as long as its primary key exists, you can recreate a deleted multi-Region replica key. For details, see [Deleting multi-Region keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-delete.html).

**Scheduling and canceling key deletion**
-----------------------------------------

The following procedures describe how to schedule key deletion and cancel key deletion of single-Region AWS KMS keys (KMS keys) in AWS KMS using the AWS Management Console, the AWS CLI, and the AWS SDK for Java.

For information about scheduling the deletion of multi-Region keys, see [Deleting multi-Region keys](https://docs.aws.amazon.com/kms/latest/developerguide/multi-region-keys-delete.html).

Deleting a KMS key is destructive and potentially dangerous. You should proceed only when you are sure that you don't need to use the KMS key anymore and won't need to use it in the future. If you are not sure, you should [disable the KMS key](https://docs.aws.amazon.com/kms/latest/developerguide/enabling-keys.html) instead of deleting it.

Before you can delete a KMS key, you must have permission to do so. If you rely on the key policy alone to specify AWS KMS permissions, you might need to add additional permissions before you can delete the KMS key. For information about adding these permissions, go to [Adding permission to schedule and cancel key deletion](https://docs.aws.amazon.com/kms/latest/developerguide/deleting-keys.html#deleting-keys-adding-permission).

AWS KMS records an entry in your AWS CloudTrail log when you [schedule deletion](https://docs.aws.amazon.com/kms/latest/developerguide/ct-schedule-key-deletion.html) of the KMS key and when the [KMS key is actually deleted](https://docs.aws.amazon.com/kms/latest/developerguide/ct-delete-key.html).

**Scheduling and canceling key deletion (console)**
---------------------------------------------------

In the AWS Management Console, you can schedule and cancel the deletion of multiple KMS keys at one time.

**To schedule key deletion**

1. Sign in to the AWS Management Console and open the AWS Key Management Service (AWS KMS) console at <https://console.aws.amazon.com/kms>
2. To change the AWS Region, use the Region selector in the upper-right corner of the page.
3. In the navigation pane, choose **Customer managed keys**
4. Select the check box next to the KMS key that you want to delete.
5. Choose **Key actions**, **Schedule key deletion**.
6. Read and consider the warning, and the information about canceling the deletion during the waiting period. If you decide to cancel the deletion, at the bottom of the page, choose **Cancel**.
7. For **Waiting period (in days)**, enter a number of days between 7 and 30.
8. Review the KMS keys that you are deleting.
9. Select the check box next to **Confirm you want to schedule this key for deletion in** `&lt;number of days&gt;` **days.**.
10. Choose **Schedule deletion**.
11. The KMS key status changes to **Pending deletion**.

**To cancel key deletion**

1. Open the AWS KMS console at <https://console.aws.amazon.com/kms>
2. To change the AWS Region, use the Region selector in the upper-right corner of the page.
3. In the navigation pane, choose **Customer managed keys**.
4. Select the check box next to the KMS key that you want to recover.
5. Choose **Key actions**, **Cancel key deletion**.

The KMS key status changes from **Pending deletion** to **Disabled**. To use the KMS key, you must [enable it](https://docs.aws.amazon.com/kms/latest/developerguide/enabling-keys.html).Adding permission to schedule and cancel key deletion

If you use IAM policies to allow AWS KMS permissions, all IAM users and roles that have AWS administrator access (`"Action": "*"`) or AWS KMS full access (`"Action": "kms:*"`) are already allowed to schedule and cancel key the deletion of KMS keys. If you rely on the key policy alone to allow AWS KMS permissions, you might need to add additional permissions to allow your IAM users and roles to delete KMS keys. You can add those permissions in the AWS KMS console or by using the AWS KMS API.

### **Adding permission to schedule and cancel key deletion (console)**

You can use the AWS Management Console to add permissions for scheduling and canceling key deletion.

1. Sign in to the AWS Management Console and open the AWS Key Management Service (AWS KMS) console at <https://console.aws.amazon.com/kms>
2. To change the AWS Region, use the Region selector in the upper-right corner of the page.
3. In the navigation pane, choose **Customer managed keys**.
4. Choose the alias or key ID of the KMS key whose permissions you want to change.
5. Choose the **Key policy** tab. Under **Key deletion**, select **Allow key administrators to delete this key** and then choose **Save changes**.

If you do not see the **Allow key administrators to delete this key** option, this usually means that you have changed this key policy using the AWS KMS API. In this case, you must update the key policy document manually. Add the `kms:ScheduleKeyDeletion` and `kms:CancelKeyDeletion` permissions to the key administrators statement (`"Sid": "Allow access for Key Administrators"`) in the key policy, and then choose **Save changes**.