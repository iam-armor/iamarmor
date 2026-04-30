# Policy with a wildcard action — foundation for Week 2 rules.
resource "aws_iam_policy" "wildcard" {
  name   = "wildcard-policy"
  policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":[\"*\"],\"Resource\":\"*\"}]}"
}
