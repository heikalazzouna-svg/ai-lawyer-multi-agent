# ──────────────────────────────────────────────────────────────────────────────
# Outputs — Connection strings and URLs exported after `terraform apply`
# ──────────────────────────────────────────────────────────────────────────────

output "api_url" {
  description = "Public URL of the AI Lawyer API (via ALB)"
  value       = "http://${aws_lb.main.dns_name}/health"
}

output "database_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "database_connection_string" {
  description = "Full PostgreSQL connection string for the API"
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/ailawyer"
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis connection endpoint"
  value       = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${aws_elasticache_cluster.redis.cache_nodes[0].port}"
  sensitive   = true
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "vpc_id" {
  description = "ID of the provisioned VPC"
  value       = aws_vpc.main.id
}
