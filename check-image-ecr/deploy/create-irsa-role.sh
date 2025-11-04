#!/usr/bin/env bash
set -euo pipefail

# Create IAM Role and Policy for IRSA, then annotate Kubernetes ServiceAccount.
# Defaults can be overridden via flags or environment variables.
#
# Usage examples:
#   bash deploy/create-irsa-role.sh -c my-eks -r ap-southeast-1 -a 058264243496 \
#     -n digigold -s check-image-ecr-sa -R check-image-ecr-irsa-role -P check-image-ecr-describe
#
# Required: aws cli, kubectl. Optional: eksctl (to associate OIDC provider automatically).

ACCOUNT_ID="${ACCOUNT_ID:-058264243496}"
REGION="${REGION:-ap-southeast-1}"
CLUSTER_NAME="${CLUSTER_NAME:-}"
NAMESPACE="${NAMESPACE:-digigold}"
SA_NAME="${SA_NAME:-check-image-ecr-sa}"
ROLE_NAME="${ROLE_NAME:-check-image-ecr-irsa-role}"
POLICY_NAME="${POLICY_NAME:-check-image-ecr-describe}"

usage() {
  echo "Usage: $0 -c <cluster_name> [-r <region>] [-a <account_id>] [-n <namespace>] [-s <service_account>] [-R <role_name>] [-P <policy_name>]"
  exit 1
}

while getopts ":c:r:a:n:s:R:P:" opt; do
  case "$opt" in
    c) CLUSTER_NAME="$OPTARG" ;;
    r) REGION="$OPTARG" ;;
    a) ACCOUNT_ID="$OPTARG" ;;
    n) NAMESPACE="$OPTARG" ;;
    s) SA_NAME="$OPTARG" ;;
    R) ROLE_NAME="$OPTARG" ;;
    P) POLICY_NAME="$OPTARG" ;;
    *) usage ;;
  esac
done

if [[ -z "$CLUSTER_NAME" ]]; then
  echo "Error: cluster name is required" >&2
  usage
fi

command -v aws >/dev/null 2>&1 || { echo "Error: aws CLI not found" >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found" >&2; exit 1; }

echo "Using settings:" 
echo "  ACCOUNT_ID=$ACCOUNT_ID"
echo "  REGION=$REGION"
echo "  CLUSTER_NAME=$CLUSTER_NAME"
echo "  NAMESPACE=$NAMESPACE"
echo "  SA_NAME=$SA_NAME"
echo "  ROLE_NAME=$ROLE_NAME"
echo "  POLICY_NAME=$POLICY_NAME"

echo "Fetching EKS cluster OIDC issuer..."
OIDC_ISSUER=$(aws eks describe-cluster --name "$CLUSTER_NAME" --region "$REGION" --query "cluster.identity.oidc.issuer" --output text)
OIDC_ID=${OIDC_ISSUER##*/}
PROVIDER_ARN="arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID"

echo "OIDC issuer: $OIDC_ISSUER"
echo "OIDC provider ARN: $PROVIDER_ARN"

HAS_PROVIDER=$(aws iam list-open-id-connect-providers --query "OpenIDConnectProviderList[?Arn=='$PROVIDER_ARN'].Arn" --output text || true)
if [[ -z "$HAS_PROVIDER" ]]; then
  echo "OIDC provider not found in IAM. Attempting to associate via eksctl (if available)..."
  if command -v eksctl >/dev/null 2>&1; then
    eksctl utils associate-iam-oidc-provider --cluster "$CLUSTER_NAME" --region "$REGION" --approve
  else
    echo "Warning: eksctl not installed. Please ensure OIDC provider exists, or install eksctl and re-run." >&2
  fi
fi

TMP_TRUST=$(mktemp)
cat > "$TMP_TRUST" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$ACCOUNT_ID:oidc-provider/oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID:sub": "system:serviceaccount:$NAMESPACE:$SA_NAME",
          "oidc.eks.$REGION.amazonaws.com/id/$OIDC_ID:aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

echo "Creating or updating IAM role $ROLE_NAME..."
set +e
ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text 2>/dev/null)
set -e
if [[ -z "$ROLE_ARN" || "$ROLE_ARN" == "None" ]]; then
  aws iam create-role --role-name "$ROLE_NAME" --assume-role-policy-document file://"$TMP_TRUST" >/dev/null
  ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)
  echo "Created role: $ROLE_ARN"
else
  aws iam update-assume-role-policy --role-name "$ROLE_NAME" --policy-document file://"$TMP_TRUST"
  echo "Updated role trust policy: $ROLE_ARN"
fi

rm -f "$TMP_TRUST"

TMP_POLICY=$(mktemp)
cat > "$TMP_POLICY" <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ecr:DescribeImages"],
      "Resource": ["arn:aws:ecr:$REGION:$ACCOUNT_ID:repository/*"]
    }
  ]
}
EOF

echo "Creating or retrieving IAM policy $POLICY_NAME..."
set +e
POLICY_ARN=$(aws iam list-policies --scope Local --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" --output text 2>/dev/null)
set -e
if [[ -z "$POLICY_ARN" || "$POLICY_ARN" == "None" ]]; then
  POLICY_ARN=$(aws iam create-policy --policy-name "$POLICY_NAME" --policy-document file://"$TMP_POLICY" --query 'Policy.Arn' --output text)
  echo "Created policy: $POLICY_ARN"
else
  echo "Using existing policy: $POLICY_ARN"
fi

rm -f "$TMP_POLICY"

echo "Attaching policy to role..."
set +e
aws iam attach-role-policy --role-name "$ROLE_NAME" --policy-arn "$POLICY_ARN" 2>/dev/null || true
set -e

echo "Annotating Kubernetes ServiceAccount $NAMESPACE/$SA_NAME with role ARN..."
kubectl annotate sa "$SA_NAME" -n "$NAMESPACE" eks.amazonaws.com/role-arn="$ROLE_ARN" --overwrite

echo "Done. Summary:"
echo "  ROLE_ARN=$ROLE_ARN"
echo "  POLICY_ARN=$POLICY_ARN"
echo "You can verify by running:"
echo "  kubectl get sa $SA_NAME -n $NAMESPACE -o yaml | grep eks.amazonaws.com/role-arn"