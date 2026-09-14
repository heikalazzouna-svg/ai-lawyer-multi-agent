# ──────────────────────────────────────────────────────────────────────────────
# Variables — Parameterized Infrastructure Configuration
# ──────────────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region to deploy resources into"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming and tagging"
  type        = string
  default     = "ai-lawyer"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# ── Database ─────────────────────────────────────────────────────────────────

variable "db_instance_class" {
  description = "RDS instance type for PostgreSQL"
  type        = string
  default     = "db.t3.micro"
}

variable "db_username" {
  description = "Master username for the RDS instance"
  type        = string
  default     = "ailawyer_admin"
  sensitive   = true
}

variable "db_password" {
  description = "Master password for the RDS instance"
  type        = string
  sensitive   = true
}

# ── Redis ────────────────────────────────────────────────────────────────────

variable "redis_node_type" {
  description = "ElastiCache node type for Redis"
  type        = string
  default     = "cache.t3.micro"
}

# ── Application ──────────────────────────────────────────────────────────────

variable "groq_api_key" {
  description = "API key for the Groq LLM provider"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "Secret key for JWT token signing"
  type        = string
  sensitive   = true
}
