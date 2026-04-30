# IAM010 PASS — attaches a scoped read-only policy, not AdministratorAccess
resource "aws_iam_role_policy_attachment" "example" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
