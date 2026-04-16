.DEFAULT_GOAL := help

# Declare that these commands are not physical files
.PHONY: help env tf-init tf-plan tf-apply tf-destroy up down

help: ## Show this list of available commands
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Copy environment variable templates (.env.example and terraform.tfvars.example)
	cp .env.example .env
	cd terraform && cp terraform.tfvars.example terraform.tfvars
	@echo "Files copied successfully! Do not forget to fill in your actual data."

tf-init: ## Initialize the Terraform working directory
	cd terraform && terraform init

tf-plan: ## Generate and show the infrastructure execution plan in GCP
	cd terraform && terraform plan

tf-apply: ## Apply the Terraform configuration (-auto-approve)
	cd terraform && terraform apply -auto-approve

tf-destroy: ## Destroy all infrastructure provisioned by Terraform (-auto-approve)
	cd terraform && terraform destroy -auto-approve

up: ## Run the full Airflow pipeline: build, init, up, and setup.sh
	docker compose build
	docker compose up airflow-init
	docker compose up -d
	bash setup.sh

down: ## Stop and remove all containers managed by Docker Compose
	docker compose down

clean: ## Stop containers and DESTROY volumes (Resets all Airflow metadata/history)
	docker compose down -v
	@echo "Volumes destroyed! Airflow is completely reset."
