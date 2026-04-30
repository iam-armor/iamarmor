# Uses a hardcoded JSON string so that policy_document parsing can be tested.
resource "aws_iam_policy" "example" {
  name        = "example-policy"
  description = "An example policy"
  policy      = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"Resource\":\"arn:aws:s3:::example-bucket/*\"}]}"
}
