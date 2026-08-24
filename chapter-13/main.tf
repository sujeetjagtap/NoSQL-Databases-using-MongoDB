# Lab 13.1 - Terraform for MongoDB Atlas# Requires: Terraform >= 1.5, Atlas API keys in environment variables## --- Provider Setup ---terraform {
  required_version = ">= 1.5.0"
  required_providers {
    mongodbatlas = {
      source  = "mongodb/mongodbatlas"
      version = "~> 1.16"
    }
  }
}# --- Atlas Project ---resource "mongodbatlas_project" "nosql_labs" {
  name   = "NoSQL Labs - Training"
  org_id = var.atlas_org_id
}# --- Free Tier Cluster ---resource "mongodbatlas_cluster" "training" {
  project_id   = mongodbatlas_project.nosql_labs.id
  name         = "training-cluster"
  cluster_type = "REPLICASET"
  provider_name               = "AWS"
  provider_region_name        = "AP_SOUTH_1"  # Mumbai
  serverless                  = false
  cloud_backup                = false  # free tier has no backup
  auto_scaling_disk_gb_enabled = true
  mongo_db_major_version       = "7.0"
  # Free tier specs
  provider_instance_size_name = "M0"
}# --- Database User ---resource "mongodbatlas_database_user" "lab_user" {
  project_id = mongodbatlas_project.nosql_labs.id
  username   = "lab_user"
  password   = var.atlas_user_password
  auth_database_name = "admin"
  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }
}# --- IP Access (allow all for training) ---resource "mongodbatlas_ip_access_list" "allow_all" {
  project_id = mongodbatlas_project.nosql_labs.id
  cidr_block = "0.0.0.0/0"
  comment    = "Allow all IPs for training (NOT for production)"
}# --- Outputs ---output "connection_string" {
  value       = mongodbatlas_cluster.training.connection_strings[0].standard_srv
  description = "MongoDB Atlas connection string"
}output "cluster_uri" {
  value = "mongodb+srv://lab_user:${var.atlas_user_password}@${mongodbatlas_cluster.training.connection_strings[0].standard_srv}/?retryWrites=true&w=majority"
  sensitive = true
}
# --- Variables ---variable "atlas_org_id" {
  description = "MongoDB Atlas Organization ID"
  type        = string
}variable "atlas_user_password" {
  description = "Password for the lab database user"
  type        = string
  sensitive   = true
}
