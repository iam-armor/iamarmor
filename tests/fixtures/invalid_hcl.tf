# Intentionally malformed HCL — missing closing brace and quote.
resource "aws_iam_policy" "broken" {
  name = "broken
