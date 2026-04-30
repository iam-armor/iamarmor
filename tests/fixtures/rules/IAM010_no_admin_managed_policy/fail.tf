# IAM010 FAIL — attaches AdministratorAccess
resource "aws_iam_role_policy_attachment" "bad" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
