# IAM007 FAIL — assume_role_policy with wildcard principal
resource "aws_iam_role" "bad" {
  name                 = "bad"
  max_session_duration = 3600
  assume_role_policy   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"sts:AssumeRole\"}]}"
}
