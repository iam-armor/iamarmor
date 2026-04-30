# Fixture for testing policy attachment resource extraction
resource "aws_iam_role_policy_attachment" "role_attach" {
  role       = "my-role"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_user_policy_attachment" "user_attach" {
  user       = "my-user"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_group_policy_attachment" "group_attach" {
  group      = "my-group"
  policy_arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}
