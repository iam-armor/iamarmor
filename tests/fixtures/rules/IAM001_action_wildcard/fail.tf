# IAM001 FAIL — wildcard action
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"*\",\"Resource\":\"*\"}]}"
}
