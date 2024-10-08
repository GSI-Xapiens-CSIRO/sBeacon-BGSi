output "cloudfront-url" {
  value       = "https://${aws_cloudfront_distribution.bui-s3-distribution.domain_name}"
  description = "Cloud front URL"
}