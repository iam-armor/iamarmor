# IAM007 PASS — assume_role_policy with concrete service principal
resource "aws_iam_role" "example" {
  name                 = "example"
  max_session_duration = 3600
  assume_role_policy   = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"
}
