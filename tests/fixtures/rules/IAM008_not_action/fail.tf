# IAM008 FAIL — NotAction in Allow statement
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"NotAction\":[\"iam:*\"],\"Resource\":\"*\"}]}"
}
