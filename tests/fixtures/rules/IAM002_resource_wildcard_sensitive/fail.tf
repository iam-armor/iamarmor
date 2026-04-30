# IAM002 FAIL — resource wildcard with sensitive action (s3:*)
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:*\"],\"Resource\":\"*\"}]}"
}
