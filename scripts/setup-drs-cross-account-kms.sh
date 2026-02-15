#!/bin/bash
#===============================================================================
# DRS Cross-Account KMS Setup & Multi-Region Key Replication
#
# Updates existing CMK key policies on both staging accounts to allow
# the target account to recover extended source servers, then replicates
# the multi-region keys to us-east-1, us-west-1, and us-west-2.
#
# Uses AWS CLI --profile to authenticate to each staging account.
#
# Accounts:
#   Target:     WorkloadsDev   - 851725249649
#   Staging 01: DRS Staging 01 - 338552098570
#   Staging 02: DRS Staging 02 - 254527609550
#
# Usage:
#   ./scripts/setup-drs-cross-account-kms.sh
#   ./scripts/setup-drs-cross-account-kms.sh --staging1-only
#   ./scripts/setup-drs-cross-account-kms.sh --staging2-only
#   ./scripts/setup-drs-cross-account-kms.sh --policy-only
#   ./scripts/setup-drs-cross-account-kms.sh --replicate-only
#   ./scripts/setup-drs-cross-account-kms.sh --dry-run
#===============================================================================
set -e

TARGET_ACCOUNT_ID="851725249649"
STAGING1_ACCOUNT_ID="338552098570"
STAGING1_KEY_ID="mrk-c243f2b1f03e42a8a4864d35b5cdd73a"
STAGING1_PROFILE="338552098570_AWSAdministratorAccess"
STAGING2_ACCOUNT_ID="254527609550"
STAGING2_KEY_ID="mrk-aceb67fc72ba42758b8c5a75d1d51659"
STAGING2_PROFILE="254527609550_AWSAdministratorAccess"
TARGET_PROFILE="851725249649_AWSAdministratorAccess"
SOURCE_REGION="us-east-2"
REPLICA_REGIONS=("us-east-1" "us-west-1" "us-west-2")
ALL_REGIONS=("us-east-2" "us-east-1" "us-west-1" "us-west-2")

DRY_RUN=false
DO_STAGING1=true
DO_STAGING2=true
DO_POLICY=true
DO_REPLICATE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --staging1-only) DO_STAGING2=false; shift ;;
        --staging2-only) DO_STAGING1=false; shift ;;
        --policy-only) DO_REPLICATE=false; shift ;;
        --replicate-only) DO_POLICY=false; shift ;;
        --dry-run) DRY_RUN=true; shift ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

log_info() { echo -e "\033[0;34m[INFO]\033[0m $1"; }
log_ok()   { echo -e "\033[0;32m[OK]\033[0m $1"; }
log_warn() { echo -e "\033[0;33m[WARN]\033[0m $1"; }
log_err()  { echo -e "\033[0;31m[ERROR]\033[0m $1"; }
trap 'rm -f /tmp/kms-policy-*.json' EXIT

build_key_policy() {
    local sa="$1" ta="$2"
    local ec2vs="" drsv=""
    for r in "${ALL_REGIONS[@]}"; do
        [[ -n "$ec2vs" ]] && ec2vs="${ec2vs}," && drsv="${drsv},"
        ec2vs="${ec2vs}\"ec2.${r}.amazonaws.com\""
        drsv="${drsv}\"drs.${r}.amazonaws.com\""
    done
    cat << POLICY
{
  "Version": "2012-10-17",
  "Id": "drs-cross-account-key-policy",
  "Statement": [
    {
      "Sid": "EnableIAMUserPermissions",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::${sa}:root"},
      "Action": "kms:*",
      "Resource": "*"
    },
    {
      "Sid": "AllowDRSStagingRoleToShareSnapshots",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::${sa}:role/service-role/DRSStagingAccountRole_${ta}"},
      "Action": "kms:ReEncrypt*",
      "Resource": "*",
      "Condition": {"StringEquals": {"kms:CallerAccount": "${sa}", "kms:ViaService": [${ec2vs}]}}
    },
    {
      "Sid": "AllowTargetAccountToUseKeyViaEC2",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::${ta}:root"},
      "Action": "kms:ReEncrypt*",
      "Resource": "*",
      "Condition": {"StringEquals": {"kms:CallerAccount": "${ta}", "kms:ViaService": [${ec2vs}]}}
    },
    {
      "Sid": "AllowTargetAccountCryptoOps",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::${ta}:root"},
      "Action": ["kms:Encrypt","kms:Decrypt","kms:GenerateDataKey*","kms:DescribeKey"],
      "Resource": "*"
    },
    {
      "Sid": "AllowTargetAccountGrants",
      "Effect": "Allow",
      "Principal": {"AWS": "arn:aws:iam::${ta}:root"},
      "Action": ["kms:CreateGrant","kms:ListGrants","kms:RevokeGrant"],
      "Resource": "*",
      "Condition": {"Bool": {"kms:GrantIsForAWSResource": "true"}}
    },
    {
      "Sid": "AllowDRSService",
      "Effect": "Allow",
      "Principal": {"Service": "drs.amazonaws.com"},
      "Action": ["kms:Decrypt","kms:DescribeKey","kms:CreateGrant","kms:GenerateDataKey"],
      "Resource": "*",
      "Condition": {"StringEquals": {"kms:ViaService": [${ec2vs},${drsv}]}}
    }
  ]
}
POLICY
}

update_key_policy() {
    local staging_name="$1" staging_id="$2" key_id="$3" profile="$4"
    echo ""
    echo "======================================================"
    echo " Updating Key Policy: $staging_name ($staging_id)"
    echo " Key: $key_id | Profile: $profile"
    echo "======================================================"

    log_info "Verifying credentials for $staging_name..."
    local acct
    acct=$(AWS_PAGER="" aws sts get-caller-identity --profile "$profile" --query 'Account' --output text 2>&1) || {
        log_err "Cannot authenticate with profile $profile: $acct"; return 1
    }
    if [[ "$acct" != "$staging_id" ]]; then
        log_err "Profile $profile is for account $acct, expected $staging_id"; return 1
    fi
    log_ok "Authenticated to $staging_name ($acct)"

    log_info "Verifying key..."
    local key_state
    key_state=$(AWS_PAGER="" aws kms describe-key --profile "$profile" --key-id "$key_id" --region "$SOURCE_REGION" \
        --query 'KeyMetadata.KeyState' --output text 2>&1) || {
        log_err "Cannot access key: $key_state"; return 1
    }
    log_ok "Key state: $key_state"

    log_info "Backing up current policy..."
    AWS_PAGER="" aws kms get-key-policy --profile "$profile" --key-id "$key_id" \
        --policy-name default --region "$SOURCE_REGION" --output text \
        > "/tmp/kms-policy-backup-${staging_id}.json"
    log_ok "Backup: /tmp/kms-policy-backup-${staging_id}.json"

    local policy_file="/tmp/kms-policy-${staging_id}.json"
    build_key_policy "$staging_id" "$TARGET_ACCOUNT_ID" > "$policy_file"

    if [[ "$DRY_RUN" == true ]]; then
        log_info "[DRY-RUN] Would apply policy to $key_id:"
        cat "$policy_file"
        return 0
    fi

    log_info "Applying key policy..."
    AWS_PAGER="" aws kms put-key-policy --profile "$profile" --key-id "$key_id" \
        --policy-name default --policy "file://$policy_file" --region "$SOURCE_REGION" 2>&1 || {
        log_err "Failed to apply policy. Backup: /tmp/kms-policy-backup-${staging_id}.json"; return 1
    }
    log_ok "Key policy updated for $staging_name"
}

replicate_key() {
    local staging_name="$1" staging_id="$2" key_id="$3" profile="$4"
    echo ""
    echo "======================================================"
    echo " Replicating MRK: $staging_name"
    echo " Key: $key_id -> ${REPLICA_REGIONS[*]}"
    echo "======================================================"

    for target_region in "${REPLICA_REGIONS[@]}"; do
        local existing
        existing=$(AWS_PAGER="" aws kms describe-key --profile "$profile" --key-id "$key_id" \
            --region "$target_region" --query 'KeyMetadata.KeyId' --output text 2>/dev/null || echo "")

        if [[ -n "$existing" && "$existing" != "None" ]]; then
            log_ok "Replica exists in $target_region"
            continue
        fi

        if [[ "$DRY_RUN" == true ]]; then
            log_info "[DRY-RUN] Would replicate $key_id to $target_region"
            continue
        fi

        log_info "Replicating to $target_region..."
        local replica_arn
        replica_arn=$(AWS_PAGER="" aws kms replicate-key --profile "$profile" \
            --key-id "$key_id" --replica-region "$target_region" --region "$SOURCE_REGION" \
            --description "DRS EBS encryption key replica - $staging_name" \
            --tags "TagKey=Purpose,TagValue=DRS-Cross-Account" "TagKey=SourceRegion,TagValue=$SOURCE_REGION" \
            --query 'ReplicaKeyMetadata.Arn' --output text 2>&1) || {
            log_err "Failed to replicate to $target_region: $replica_arn"
            continue
        }
        log_ok "Replicated to $target_region: $replica_arn"
    done
}

verify_setup() {
    local staging_name="$1" staging_id="$2" key_id="$3" profile="$4"
    echo ""
    echo "======================================================"
    echo " Verifying: $staging_name"
    echo "======================================================"

    for region in "${ALL_REGIONS[@]}"; do
        local state
        state=$(AWS_PAGER="" aws kms describe-key --profile "$profile" --key-id "$key_id" \
            --region "$region" --query 'KeyMetadata.KeyState' --output text 2>/dev/null || echo "NOT_FOUND")
        if [[ "$state" == "Enabled" ]]; then
            log_ok "$region: Enabled"
        else
            log_warn "$region: $state"
        fi
    done

    local policy
    policy=$(AWS_PAGER="" aws kms get-key-policy --profile "$profile" --key-id "$key_id" \
        --policy-name default --region "$SOURCE_REGION" --output text 2>/dev/null || echo "")

    if echo "$policy" | grep -q "$TARGET_ACCOUNT_ID"; then
        log_ok "Policy includes target account ($TARGET_ACCOUNT_ID)"
    else
        log_err "Policy does NOT include target account"
    fi

    if echo "$policy" | grep -q "DRSStagingAccountRole"; then
        log_ok "Policy includes DRSStagingAccountRole"
    else
        log_warn "DRSStagingAccountRole not in policy (create trusted account in DRS console first)"
    fi
}

#===============================================================================
# Main
#===============================================================================
echo "######################################################"
echo "# DRS Cross-Account KMS Setup & MRK Replication"
echo "######################################################"
echo ""
echo "Target Account:  $TARGET_ACCOUNT_ID (WorkloadsDev)"
echo "Staging 01:      $STAGING1_ACCOUNT_ID (Key: $STAGING1_KEY_ID)"
echo "Staging 02:      $STAGING2_ACCOUNT_ID (Key: $STAGING2_KEY_ID)"
echo "Source Region:   $SOURCE_REGION"
echo "Replica Regions: ${REPLICA_REGIONS[*]}"
echo "Dry Run:         $DRY_RUN"
echo ""

if [[ "$DO_STAGING1" == true ]]; then
    [[ "$DO_POLICY" == true ]] && update_key_policy "Staging 01" "$STAGING1_ACCOUNT_ID" "$STAGING1_KEY_ID" "$STAGING1_PROFILE"
    [[ "$DO_REPLICATE" == true ]] && replicate_key "Staging 01" "$STAGING1_ACCOUNT_ID" "$STAGING1_KEY_ID" "$STAGING1_PROFILE"
    verify_setup "Staging 01" "$STAGING1_ACCOUNT_ID" "$STAGING1_KEY_ID" "$STAGING1_PROFILE"
fi

if [[ "$DO_STAGING2" == true ]]; then
    [[ "$DO_POLICY" == true ]] && update_key_policy "Staging 02" "$STAGING2_ACCOUNT_ID" "$STAGING2_KEY_ID" "$STAGING2_PROFILE"
    [[ "$DO_REPLICATE" == true ]] && replicate_key "Staging 02" "$STAGING2_ACCOUNT_ID" "$STAGING2_KEY_ID" "$STAGING2_PROFILE"
    verify_setup "Staging 02" "$STAGING2_ACCOUNT_ID" "$STAGING2_KEY_ID" "$STAGING2_PROFILE"
fi

echo ""
echo "######################################################"
echo "# Complete"
echo "######################################################"
if [[ "$DRY_RUN" == true ]]; then
    echo "DRY RUN - No changes made."
else
    echo ""
    echo "Next Steps:"
    echo "  1. In each staging account DRS console, add $TARGET_ACCOUNT_ID as trusted account"
    echo "     and create the Staging role (DRSStagingAccountRole_$TARGET_ACCOUNT_ID)"
    echo ""
    echo "  2. Set DRS replication to CUSTOM encryption in each staging account:"
    echo "     Staging 01: aws drs update-replication-configuration-template --profile $STAGING1_PROFILE \\"
    echo "       --region $SOURCE_REGION --ebs-encryption CUSTOM \\"
    echo "       --ebs-encryption-key-arn arn:aws:kms:$SOURCE_REGION:$STAGING1_ACCOUNT_ID:key/$STAGING1_KEY_ID"
    echo ""
    echo "     Staging 02: aws drs update-replication-configuration-template --profile $STAGING2_PROFILE \\"
    echo "       --region $SOURCE_REGION --ebs-encryption CUSTOM \\"
    echo "       --ebs-encryption-key-arn arn:aws:kms:$SOURCE_REGION:$STAGING2_ACCOUNT_ID:key/$STAGING2_KEY_ID"
    echo ""
    echo "  3. Initialize DRS in target account if not done:"
    echo "     aws drs initialize-service --profile $TARGET_PROFILE --region $SOURCE_REGION"
    echo ""
    echo "  4. Create extended source servers from target account DRS console"
fi
echo "######################################################"
