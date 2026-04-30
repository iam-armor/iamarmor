# IAM005 PASS — PassRole scoped to a specific role ARN
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"iam:PassRole\"],\"Resource\":\"arn:aws:iam::123456789012:role/my-specific-role\"}]}"
}
