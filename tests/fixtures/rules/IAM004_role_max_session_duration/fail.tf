# IAM004 FAIL — role missing max_session_duration
resource "aws_iam_role" "bad" {
  name               = "bad"
  assume_role_policy = "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Principal\":{\"Service\":\"lambda.amazonaws.com\"},\"Action\":\"sts:AssumeRole\"}]}"
}
