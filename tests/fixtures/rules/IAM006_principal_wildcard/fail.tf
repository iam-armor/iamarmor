# IAM006 FAIL — wildcard Principal
resource "aws_iam_policy" "bad" {
  name   = "bad"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"sts:AssumeRole\",\"Resource\":\"*\"}]}"
}
