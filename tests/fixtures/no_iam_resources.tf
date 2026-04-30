# Contains only non-IAM resources — extractor should return an empty list.
resource "aws_s3_bucket" "example" {
  bucket = "my-example-bucket"
}

resource "aws_s3_bucket_versioning" "example" {
  bucket = "my-example-bucket"
  versioning_configuration {
    status = "Enabled"
  }
}
