# IAM008 PASS — no NotAction
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::my-bucket/*\"}]}"
}
