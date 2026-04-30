# IAM002 PASS — resource wildcard but non-sensitive action
resource "aws_iam_policy" "example" {
  name   = "example"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"ec2:DescribeInstances\"],\"Resource\":\"*\"}]}"
}
