# Define-CloudWatch-Alarms-and-Metrics-via-Landing-Zone-Accelerator

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/4867098158/Define-CloudWatch-Alarms-and-Metrics-via-Landing-Zone-Accelerator

**Created by:** Chris Falk on June 16, 2025  
**Last modified by:** Chris Falk on June 16, 2025 at 02:35 AM

---

**Purpose**
-----------

This document describes the process in deploying the AWS CloudWatch Alarms with Metric Filters.

**Prerequisites**
-----------------

Before deploying out these controls in an AWS environment, it’s important that the following pre-requisites are met.

* The Region Design page **1.2 [Decision] AWS Region Design** should be referenced and baselined.

  + Establish region(s) in global-config.yaml
* The Landing Zone OU Characteristics Design page **1.1 [Decision] Foundational Account Design** should be referenced and baselined.

  + Establish Organization Unit(s) (OU) in organization-config.yaml
* The Detective Controls design page **[Decision] Detective and Preventative Controls Design** should be referenced and baselined.

**Parameter Values**
--------------------

The following parameters are a description of the attributes as well as the allowed values

### Cloud Watch Metrics

* **filterName**: The name of the filter.

  + Type: String
  + Constraints: Minimum length of 1. Maximum length of 255
* **logGroup:** The log group to create the filter on.

  + Type: String
* **filterPattern**: Pattern to search for log events.

  + Type: Filter Pattern
* **metricName**: The name for the metric associated with the alarm.

  + Type: String
  + Constraints: Minimum length of 1. Maximum length of 255
* **metricNamespace:** The namespace for the metric associated specified in `MetricName`.

  + Type**:** String
  + Constraints: Minimum length of 1. Maximum length of 255.
  + Pattern: [^:].\*
* **metricValue:** The value to emit for the metric. Can either be a literal number, or the name of a field in the structure to take the value from the matched event. If you want to specify a field from a matched JSON structure, use ‘$.fieldName’, and make sure the field is in the pattern (if only as ‘$.fieldName “\*”').

  + Type: String

### Cloud Watch Alarms

* **alarmName**: Name of the alarm.

  + Type: String
  + Constraints: Minimum length of 1. Maximum length of 255.
* **alarmDescription:** The description for the alarm.

  + Type: String
  + Constraints: Minimum length of 0. Maximum length of 1024.
* **snsAlertLevel**: Set string value for severity of alert in resource. (Check with Randy on this)

  + Type: String
* **metricName:** The name for the metric associated with the alarm.

  + Type: String
  + Constraints: Minimum length of 1. Maximum length of 255
* **namespace:** The namespace for the metric associated specified in MetricName.

  + Type: String
  + Constraints: Minimum length of 1. Maximum length of 255.
  + Pattern: [^:].\*
* **comparisonOperator**: The arithmetic operation to use when comparing the specified statistic and threshold. The specified statistic value is used as the first operand.

  + Type: String
  + Value Values: `GreaterThanOrEqualToThreshold | GreaterThanThreshold | LessThanThreshold | LessThanOrEqualToThreshold | LessThanLowerOrGreaterThanUpperThreshold | LessThanLowerThreshold | GreaterThanUpperThreshold`
* **evaluationPeriods**: The number of periods over which data is compared to the specified threshold. If you are setting an alarm that requires that a number of consecutive data points be breaching to trigger the alarm, this value specifies that number. If you are setting an "M out of N" alarm, this value is the N.

  An alarm's total current evaluation period can be no longer than one day, so this number multiplied by `Period` cannot be more than 86,400 seconds.

  + Type: Integer
  + Valid Range: Minimum value of 1
* **period**: The length, in seconds, used each time the metric specified in `MetricName` is evaluated. Valid values are 10, 30, and any multiple of 60.

  + Type: Integer
  + Valid Range: Minimum value of 1
* **statistic**: The statistic for the metric specified in `MetricName`, other than percentile.

  + Type: String
  + Valid Values: `SampleCount | Average | Sum | Minimum | Maximum`
* **threshold:** The value against which the specified statistic is compared.

  + Type: Integer
* **treatMissingData**: Sets how this alarm is to handle missing data points. If `TreatMissingData` is omitted, the default behavior of `missing` is used.

  + Type: String
  + Valid Values: `breaching | notBreaching | ignore | missing`
  + Constraints: Minimum length of 1. Maximum length of 255.

**Procedure**
-------------

The following is an example of how to establish Cloud Watch Alarms with Metric filters In security-config.yaml