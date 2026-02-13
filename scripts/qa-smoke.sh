#!/bin/bash

set -euo pipefail

BASE_URL="${1:-http://localhost:8000}"
COOKIE_JAR="$(mktemp)"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -f "$COOKIE_JAR"
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

request_json() {
  local method="$1"
  local path="$2"
  local data="${3:-}"
  local out_body="$4"

  if [ -n "$data" ]; then
    status=$(curl -sS -o "$out_body" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" \
      -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
      "$BASE_URL$path" \
      -d "$data")
  else
    status=$(curl -sS -o "$out_body" -w "%{http_code}" -X "$method" \
      -H "Content-Type: application/json" \
      -b "$COOKIE_JAR" -c "$COOKIE_JAR" \
      "$BASE_URL$path")
  fi
  echo "$status"
}

parse_json_field() {
  local file="$1"
  local field_expr="$2"
  python3 -c "import json,sys; data=json.load(open(sys.argv[1])); print($field_expr)" "$file"
}

assert_status() {
  local expected="$1"
  local actual="$2"
  local label="$3"
  if [ "$expected" != "$actual" ]; then
    echo "[FAIL] $label: expected=$expected actual=$actual"
    exit 1
  fi
  echo "[PASS] $label ($actual)"
}

echo "QA Smoke 시작: $BASE_URL"

health_body="$TMP_DIR/health.json"
health_status=$(request_json GET "/health" "" "$health_body")
assert_status 200 "$health_status" "health"

suffix="$(date +%s)"
email="qa_${suffix}@example.com"
nickname="qa${suffix: -6}"
password="Aa1!aaaa"

signup_body="$TMP_DIR/signup.json"
signup_payload=$(printf '{"email":"%s","password":"%s","nickname":"%s"}' "$email" "$password" "$nickname")
signup_status=$(request_json POST "/v1/auth/signup" "$signup_payload" "$signup_body")
assert_status 201 "$signup_status" "signup"

login_body="$TMP_DIR/login.json"
login_payload=$(printf '{"email":"%s","password":"%s"}' "$email" "$password")
login_status=$(request_json POST "/v1/auth/login" "$login_payload" "$login_body")
assert_status 200 "$login_status" "login"

posts_body="$TMP_DIR/posts.json"
posts_status=$(request_json GET "/v1/posts?offset=0&limit=5" "" "$posts_body")
assert_status 200 "$posts_status" "list posts"

create_post_body="$TMP_DIR/create_post.json"
create_post_payload='{"title":"QA Smoke Post","content":"smoke test content","fileUrls":[]}'
create_post_status=$(request_json POST "/v1/posts" "$create_post_payload" "$create_post_body")
assert_status 201 "$create_post_status" "create post"

post_id=$(parse_json_field "$create_post_body" "data.get('data',{}).get('postId','')")
if [ -z "$post_id" ]; then
  echo "[FAIL] create post: postId 파싱 실패"
  exit 1
fi

echo "생성된 postId: $post_id"

update_post_body="$TMP_DIR/update_post.json"
update_post_payload='{"title":"QA Smoke Post Updated","content":"updated content","fileUrls":[]}'
update_post_status=$(request_json PATCH "/v1/posts/$post_id" "$update_post_payload" "$update_post_body")
assert_status 200 "$update_post_status" "update post"

create_comment_body="$TMP_DIR/create_comment.json"
create_comment_payload='{"content":"qa smoke comment"}'
create_comment_status=$(request_json POST "/v1/posts/$post_id/comments" "$create_comment_payload" "$create_comment_body")
assert_status 201 "$create_comment_status" "create comment"

comment_id=$(parse_json_field "$create_comment_body" "data.get('data',{}).get('commentId','')")
if [ -z "$comment_id" ]; then
  echo "[FAIL] create comment: commentId 파싱 실패"
  exit 1
fi

echo "생성된 commentId: $comment_id"

delete_comment_body="$TMP_DIR/delete_comment.json"
delete_comment_status=$(request_json DELETE "/v1/posts/$post_id/comments/$comment_id" "" "$delete_comment_body")
assert_status 200 "$delete_comment_status" "delete comment"

delete_post_body="$TMP_DIR/delete_post.json"
delete_post_status=$(request_json DELETE "/v1/posts/$post_id" "" "$delete_post_body")
assert_status 200 "$delete_post_status" "delete post"

logout_body="$TMP_DIR/logout.json"
logout_status=$(request_json POST "/v1/auth/logout" "{}" "$logout_body")
assert_status 200 "$logout_status" "logout"

echo "QA Smoke 완료"
