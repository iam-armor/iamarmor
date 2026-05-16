# iamarmor demo — VHS tape
# Regenerate: vhs docs/demo.tape
# Requires: vhs (https://github.com/charmbracelet/vhs), iamarmor installed

Output docs/demo.gif

Set Shell "bash"
Set FontSize 14
Set Width 900
Set Height 500
Set Theme "Dracula"

# Wait for shell prompt
Sleep 500ms

# Show version
Type "iamarmor --version"
Enter
Sleep 1s

# Show help
Type "iamarmor scan --help"
Enter
Sleep 2s

# Lint the test fixtures (clean pass first)
Type "iamarmor scan tests/fixtures/rules/IAM001_action_wildcard/pass.tf"
Enter
Sleep 2s

# Lint a failing fixture
Type "iamarmor scan tests/fixtures/rules/IAM001_action_wildcard/fail.tf"
Enter
Sleep 2s

# Lint a directory with multiple failing fixtures
Type "iamarmor scan tests/fixtures/rules/ --severity-threshold high"
Enter
Sleep 3s

# Show JSON output
Type "iamarmor scan tests/fixtures/rules/IAM001_action_wildcard/fail.tf --format json"
Enter
Sleep 2s

Sleep 1s
