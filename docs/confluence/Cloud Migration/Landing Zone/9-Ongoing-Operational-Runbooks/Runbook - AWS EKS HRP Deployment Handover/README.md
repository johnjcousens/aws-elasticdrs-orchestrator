# Runbook - AWS EKS HRP Deployment Handover

**Confluence Page:** https://healthedge.atlassian.net/wiki/spaces/CP1/pages/5369004033/Runbook%20-%20AWS%20EKS%20HRP%20Deployment%20Handover

**Created by:** Rahul Sharma on December 18, 2025  
**Last modified by:** Rahul Sharma on December 19, 2025 at 06:17 PM

---

HRP EKS Cluster Handover Documentation
======================================

Overview
--------

This document provides deployment instructions for the HRP EKS cluster, covering both the melissa-data and webui deployments.

---

1. Melissa-Data Deployment
--------------------------

### Prerequisites

Verify that EFS is configured on the AWS account before proceeding.

### Step 1: Create Storage Class

Apply the storage class configuration:


```bash
kubectl apply -f storage-class.yaml
```


**storage-class.yaml:**


```
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs-root-sc
provisioner: efs.csi.aws.com
parameters:
  fileSystemId: <efs-id>
reclaimPolicy: Retain
volumeBindingMode: Immediate
```


### Step 2: Create Persistent Volume

Apply the persistent volume configuration:


```
kubectl apply -f pv.yaml
```


**pv.yaml:**


```
apiVersion: v1
kind: PersistentVolume
metadata:
  name: efs-root-pv
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: efs-root-sc
  csi:
    driver: efs.csi.aws.com
    volumeHandle: <efs-id>
```


### Step 3: Deploy Melissa-Data


```
kubectl apply -f https://github.com/HE-Core/platform.cloud-engineering-eks/blob/main/melissa-data-deployment-v2.yaml
```


2. WebUI Deployment
-------------------

### Components

* he-payor-rest-adaptor
* he-payor-ui-react
* he-payor-web-ui
* hrp-designer-web

### Configuration Steps

#### Step 1: Update Docker Image Repository

Update `values.yaml` for each Helm chart to reference ECR images:


```
image:
  repository: <account-id>.dkr.ecr.us-east-1.amazonaws.com
```


#### Step 2: Configure Ingress Rules

Update the ingress configuration under `he-payor-web-ui`:

**Important: Ingress Rule Priority**

* Use `alb.ingress.kubernetes.io/group.order` to define listener rule priority
* Use `alb.ingress.kubernetes.io/group.name: payor-webui` (same across all rules to share one ALB)
* Priority ranges:

  + **payor-api-ingress**: 1-50 (highest priority)
  + **payor-websocket-ingress**: 51-99 (medium priority)
  + **payor-ui-ingress**: 100-500 (lowest priority)

**Ingress Configuration:**


```
# 1. Payor UI Ingress (Priority: 100-500)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payor-ui-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/group.name: payor-webui
    alb.ingress.kubernetes.io/group.order: "100"
    alb.ingress.kubernetes.io/healthcheck-path: /
    {{- if .Values.ingress.tls }}
    alb.ingress.kubernetes.io/certificate-arn: <ACM ARN>
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    {{- end }}
spec:
  {{- if .Values.ingress.tls }}
  tls:
  - hosts:
    - {{ .Values.ingress.tls.host }}
    secretName: {{ .Values.ingress.tls.secretName }}
  {{- end }}
  rules:
    - {{- if .Values.ingress.tls }}
      host: {{ .Values.ingress.tls.host }}
      {{- end }}
      http:
        paths:
        - path: /*
          pathType: ImplementationSpecific
          backend:
            service:
              name: {{ .Release.Name }}-he-payor-ui-react
              port:
                number: 8080
---
# 2. Payor API Ingress (Priority: 1-50)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payor-api-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/group.name: payor-webui
    alb.ingress.kubernetes.io/group.order: "5"
    alb.ingress.kubernetes.io/transforms.<he-payor-rest-adaptor service name>: >
      [
          {
              "type": "url-rewrite",
              "urlRewriteConfig": {
                  "rewrites": [
                      {
                          "regex": "/api/*",
                          "replace": "/$1"
                      }
                  ]
              }
          }
      ]
    alb.ingress.kubernetes.io/healthcheck-path: /actuator/health
    {{- if .Values.ingress.tls }}
    alb.ingress.kubernetes.io/certificate-arn: <ACM ARN>
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    {{- end }}
spec:
  {{- if .Values.ingress.tls }}
  tls:
  - hosts:
    - {{ .Values.ingress.tls.host }}
    secretName: {{ .Values.ingress.tls.secretName }}
  {{- end }}
  rules:
    - {{- if .Values.ingress.tls }}
      host: {{ .Values.ingress.tls.host }}
      {{- end }}
      http:
        paths:
        - path: /api/*
          pathType: ImplementationSpecific
          backend:
            service:
              name: {{ .Release.Name }}-he-payor-rest-adaptor
              port:
                number: 3030
---
# 3. Payor WebSocket Ingress (Priority: 51-99)
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: payor-websocket-ingress
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/group.name: payor-webui
    alb.ingress.kubernetes.io/group.order: "60"
    alb.ingress.kubernetes.io/healthcheck-path: /
    alb.ingress.kubernetes.io/success-codes: '200,400'
    {{- if .Values.ingress.tls }}
    alb.ingress.kubernetes.io/certificate-arn: <ACM ARN>
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTPS":443}]'
    {{- end }}
spec:
  {{- if .Values.ingress.tls }}
  tls:
  - hosts:
    - {{ .Values.ingress.tls.host }}
    secretName: {{ .Values.ingress.tls.secretName }}
  {{- end }}
  rules:
    - {{- if .Values.ingress.tls }}
      host: {{ .Values.ingress.tls.host }}
      {{- end }}
      http:
        paths:
        - path: /websocket/*
          pathType: ImplementationSpecific
          backend:
            service:
              name: {{ .Release.Name }}-he-payor-rest-adaptor
              port:
                number: 6010
```


#### Step 3: Update Configuration Files

**payor-web-ui values.yaml:**


```
adaptor_host_url: "<tenant_specific_adaptor_host_url>"
default_payer_server_url: "<tenant_specific_default_payer_server_url>"
```


**managerConfig.json:**


```
{
  "URL": "tenant_specific_url"
}
```


### Tenant-Specific Deployment

#### Initial Installation


```
helm install -n <tenant_namespace> <tenant_release_name> he-payor-web-ui \
  -f he-payor-web-ui/payer-webui-values.yaml \
  --set he-payor-ui-react.image.tag=<payor-ui-react-image-version> \
  --set he-payor-rest-adaptor.image.rest_adaptor.tag=<payor-rest-adaptor-image-version> \
  --set he-payor-rest-adaptor.image.websocket.tag=<payor-websocket-image-version> \
  --set adaptor_host_url=<tenant_specific_adaptor_host_url> \
  --set default_payer_server_url=<tenant_specific_default_payer_server_url> \
  --set ingress.tls.host=<tenant_specific_tls_host> \
  --set-file he-payor-rest-adaptor.runtimePropertiesFile=he-payor-web-ui/runtime.properties \
  --wait --timeout 180s
```


#### Deployment Updates


```
helm upgrade -n <tenant_namespace> <tenant_release_name> he-payor-web-ui \
  -f he-payor-web-ui/payer-webui-values.yaml \
  --set he-payor-ui-react.image.tag=<payor-ui-react-image-version> \
  --set he-payor-rest-adaptor.image.rest_adaptor.tag=<payor-rest-adaptor-image-version> \
  --set he-payor-rest-adaptor.image.websocket.tag=<payor-websocket-image-version> \
  --set adaptor_host_url=<tenant_specific_adaptor_host_url> \
  --set default_payer_server_url=<tenant_specific_default_payer_server_url> \
  --set ingress.tls.host=<tenant_specific_tls_host> \
  --set-file he-payor-rest-adaptor.runtimePropertiesFile=he-payor-web-ui/runtime.properties \
  --wait --timeout 180s
```


Configuration Placeholders
--------------------------

Replace the following placeholders with actual values:

#### Table

| Placeholder | Description |
| --- | --- |
| <efs-id> | EFS file system ID |
| <account-id> | AWS account ID |
| <ACM ARN> | AWS Certificate Manager ARN |
| <tenant\_namespace> | Kubernetes namespace for tenant |
| <tenant\_release\_name> | Helm release name for tenant |
| <payor-ui-react-image-version> | Docker image tag for UI React component |
| <payor-rest-adaptor-image-version> | Docker image tag for REST adaptor |
| <payor-websocket-image-version> | Docker image tag for WebSocket component |
| <tenant\_specific\_adaptor\_host\_url> | Tenant-specific adaptor host URL |
| <tenant\_specific\_default\_payer\_server\_url> | Tenant-specific payer server URL |