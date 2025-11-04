#!/usr/bin/env bash
set -euo pipefail
export PATH=/usr/local/bin:/usr/bin:/bin
export KUBECONFIG=~/.kube/config
# Script: Lấy SHA từ AWS ECR cho tag 'latest' bằng aws cli và so sánh
# Định dạng mỗi dòng trong /app/config.txt: deployment_name:image_uri:sha256:abcdef...
# Ví dụ: user-service:058264243496.dkr.ecr.ap-southeast-1.amazonaws.com/user-service:latest:sha256:a1b2c3...
#
# Sử dụng:
#   bash deploy/check-ecr-sha.sh                 # đọc /app/config.txt mặc định
#   CONFIG_PATH=/path/to/config.txt bash deploy/check-ecr-sha.sh
# Tuỳ chọn:
#   REGISTRY_ID (mặc định 058264243496)
#   REGION (mặc định ap-southeast-1)
#   VERBOSE=true để in chi tiết
#   ROLLOUT_ON_DIFF=true để restart deployment khi phát hiện khác biệt
#   TARGET_NAMESPACE=digigold namespace chứa deployments cần restart
#   UPDATE_CONFIG_ON_DIFF=true để ghi lại digest mới vào file config

CONFIG_PATH="${CONFIG_PATH:-/opt/check-image/config.txt}"
REGISTRY_ID="${REGISTRY_ID:-058264243496}"
REGION="${REGION:-ap-southeast-1}"
VERBOSE="${VERBOSE:-false}"
ROLLOUT_ON_DIFF="${ROLLOUT_ON_DIFF:-false}"
TARGET_NAMESPACE="${TARGET_NAMESPACE:-digigold}"
UPDATE_CONFIG_ON_DIFF="${UPDATE_CONFIG_ON_DIFF:-true}"
UPDATED_COUNT=0
NEW_LINE=""

# Helpers: timestamped logging
ts() { date "+%Y-%m-%d %H:%M:%S"; }
log() { if [[ "$VERBOSE" == "true" ]]; then echo "$(ts) $@"; fi }
out() { echo "$(ts) $@"; }

command -v aws >/dev/null 2>&1 || { out "ERROR: aws CLI chưa cài đặt" >&2; exit 1; }

if [[ ! -f "$CONFIG_PATH" ]]; then
  out "WARNING: Không tìm thấy file cấu hình: $CONFIG_PATH"
  exit 0
fi

TMP_CONFIG="$(mktemp)"

# (log helper redefined above with timestamp)

# Lấy digest của tag latest qua aws ecr list-images
get_latest_digest() {
  local repo="$1"
  /usr/local/bin/aws ecr list-images \
    --repository-name "$repo" \
    --registry-id "$REGISTRY_ID" \
    --region "$REGION" \
    --query 'imageIds[?imageTag==`latest`].imageDigest' \
    --output text 2>/dev/null || true
}

parse_and_check_line() {
  local line="$1"
  # Bỏ khoảng trắng và comment
  [[ -z "$line" ]] && { NEW_LINE="$line"; return 0; }
  [[ "$line" =~ ^# ]] && { NEW_LINE="$line"; return 0; }

  # deployment là phần trước dấu ':' đầu tiên
  local deployment="${line%%:*}"
  local rest="${line#*:}"

  # sha dạng 'sha256:...' lấy theo regex
  local sha
  if [[ "$line" =~ (sha256:[a-f0-9]+) ]]; then
    sha="${BASH_REMATCH[1]}"
  else
    out "WARNING: Dòng không hợp lệ, thiếu SHA -> $line" >&2
    NEW_LINE="$line"; return 0
  fi

  # image là phần giữa sau dấu ':' đầu tiên và trước ':sha256:'
  local image="${rest%%:sha256:*}"
  if [[ -z "$deployment" || -z "$image" ]]; then
    out "WARNING: Dòng không hợp lệ (thiếu deployment hoặc image) -> $line" >&2
    NEW_LINE="$line"; return 0
  fi

  # Từ image URI, lấy repository name: phần sau '.amazonaws.com/' và bỏ ':latest'
  local repo_part="${image##*.amazonaws.com/}"
  local repository="${repo_part%%:*}"
  if [[ -z "$repository" ]]; then
    out "WARNING: Không trích xuất được repository từ image -> $image" >&2
    NEW_LINE="$line"; return 0
  fi

  log "Check deployment=$deployment repo=$repository stored_sha=$sha"

  local latest_digest
  latest_digest="$(get_latest_digest "$repository")"

  if [[ -z "$latest_digest" || "$latest_digest" == "None" ]]; then
    out "ERROR: Không tìm thấy digest cho tag 'latest' ở repo $repository" >&2
    NEW_LINE="$deployment:$image:$sha"; return 0
  fi

  if [[ "$latest_digest" == "$sha" ]]; then
    out "OK: $deployment | $repository:latest không thay đổi ($sha)"
    NEW_LINE="$deployment:$image:$sha"
  else
    out "DIFF: $deployment | $repository:latest thay đổi -> hiện tại $latest_digest, lưu $sha"
    if [[ "$UPDATE_CONFIG_ON_DIFF" == "true" ]]; then
      NEW_LINE="$deployment:$image:$latest_digest"
      UPDATED_COUNT=$((UPDATED_COUNT+1))
    else
      NEW_LINE="$deployment:$image:$sha"
    fi
    if [[ "$ROLLOUT_ON_DIFF" == "true" ]]; then
      if ! command -v kubectl >/dev/null 2>&1; then
        out "WARNING: kubectl chưa cài đặt, bỏ qua rollout restart cho $deployment" >&2
      else
        out "Rollout restart deployment/$deployment -n $TARGET_NAMESPACE"
        # Thực hiện rollout restart và chờ trạng thái
        kubectl rollout restart deployment "$deployment" -n "$TARGET_NAMESPACE" || {
          out "ERROR: Không thể rollout restart deployment/$deployment" >&2
          return 0
        }
        # Chờ rollout status tối đa 2 phút
        kubectl rollout status deployment "$deployment" -n "$TARGET_NAMESPACE" --timeout=120s || {
          out "WARNING: Rollout status timeout cho deployment/$deployment" >&2
        }
      fi
    fi
  fi
}

while IFS= read -r line; do
  parse_and_check_line "$line"
  echo "$NEW_LINE" >> "$TMP_CONFIG"
done < "$CONFIG_PATH"

if [[ "$UPDATE_CONFIG_ON_DIFF" == "true" ]]; then
  mv "$TMP_CONFIG" "$CONFIG_PATH"
  out "Đã cập nhật $UPDATED_COUNT dòng với digest mới trong $CONFIG_PATH"
else
  rm -f "$TMP_CONFIG"
  out "Không cập nhật file cấu hình (UPDATE_CONFIG_ON_DIFF=false)."
fi