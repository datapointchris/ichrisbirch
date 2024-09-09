variable "function_name" {
  description = "The name of the Lambda function"
  type        = string
}

variable "handler" {
  description = "The handler for the Lambda function"
  type        = string
}

variable "runtime" {
  description = "The runtime for the Lambda function"
  type        = string
}

variable "role" {
  description = "The IAM role ARN for the Lambda function"
  type        = string
}

variable "filename" {
  description = "The filename of the Lambda deployment package"
  type        = string
}
