# IAM004 PASS — role with explicit max_session_duration
resource "aws_iam_role" "example" {
  name                 = "example"
  max_session_duration = 3600
  assume_role_policy   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"
}
