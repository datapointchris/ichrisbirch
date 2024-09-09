resource "aws_lambda_function" "main" {
  function_name = var.function_name
  handler       = var.handler
  runtime       = var.runtime
  role          = var.role

  source_code_hash = filebase64sha256(var.filename)
  filename         = var.filename
}

output "function_name" {
  value = aws_lambda_function.main.function_name
}
