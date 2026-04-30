# IAM009 FAIL — NotResource in Allow statement
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"s3:GetObject\"],\"NotResource\":[\"arn:aws:s3:::protected-bucket/*\"]}]}"
}
