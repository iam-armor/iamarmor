# IAM003 PASS — managed policy attachment, not an inline policy
resource "aws_iam_role_policy_attachment" "example" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
