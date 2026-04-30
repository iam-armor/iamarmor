# IAM003 FAIL — inline role policy
resource "aws_iam_role_policy" "bad" {
  name   = "bad-inline"
  role   = "my-role"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"*\"}]}"
}
