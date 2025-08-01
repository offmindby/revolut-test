# AWS Architecture Diagram - Revolut Birthday API

## Overview
This diagram shows the complete AWS infrastructure for the Revolut Birthday API application deployed using ECS Fargate with high availability and cost optimization.

## Architecture Diagram

```mermaid
graph TB
    %% Internet and DNS
    Internet["Internet"] 
    Route53["Route53<br/>DNS: revolut-api.com"]
    
    %% VPC Container
    subgraph VPC["VPC (10.0.0.0/16)"]
        %% Availability Zones
        subgraph AZ1["Availability Zone 1"]
            PublicSubnet1["Public Subnet<br/>10.0.1.0/24"]
            PrivateSubnet1["Private Subnet<br/>10.0.10.0/24"]
        end
        
        subgraph AZ2["Availability Zone 2"]
            PublicSubnet2["Public Subnet<br/>10.0.2.0/24"]
            PrivateSubnet2["Private Subnet<br/>10.0.20.0/24"]
        end
        
        %% Internet Gateway
        IGW["Internet Gateway"]
        
        %% NAT Gateway (single for cost optimization)
        NAT["NAT Gateway<br/>(Single - Cost Optimized)"]
        
        %% Load Balancer
        ALB["Application Load Balancer<br/>Port 80"]
        
        %% ECS Resources
        subgraph ECS["ECS Cluster"]
            subgraph Fargate1["Fargate Task 1<br/>(Private Subnet 1)"]
                Container1["Birthday API<br/>Port 8001"]
            end
            subgraph Fargate2["Fargate Task 2<br/>(Private Subnet 2)"]
                Container2["Birthday API<br/>Port 8001"]
            end
        end
        
        %% Security Groups
        ALBSG["ALB Security Group<br/>HTTP: 80 → Internet"]
        ECSSG["ECS Security Group<br/>8001 ← ALB Only"]
    end
    
    %% External AWS Services
    subgraph AWSServices["AWS Services"]
        ECR["ECR Repository<br/>Docker Images"]
        DynamoDB["DynamoDB<br/>users_birthdays"]
        CloudWatch["CloudWatch Logs<br/>Application Logs"]
        IAM["IAM Roles<br/>• ECS Execution Role<br/>• Application Task Role"]
    end
    
    %% CI/CD Pipeline
    subgraph CICD["CI/CD Pipeline"]
        GitHub["GitHub Actions<br/>• Test<br/>• Build<br/>• Deploy"]
    end
    
    %% Connections
    Internet --> Route53
    Route53 --> ALB
    ALB --> IGW
    IGW --> PublicSubnet1
    IGW --> PublicSubnet2
    
    PublicSubnet1 --> NAT
    NAT --> PrivateSubnet1
    NAT --> PrivateSubnet2
    
    ALB --> Container1
    ALB --> Container2
    
    Container1 --> DynamoDB
    Container2 --> DynamoDB
    Container1 --> CloudWatch
    Container2 --> CloudWatch
    
    GitHub --> ECR
    ECR --> Container1
    ECR --> Container2
    
    %% Security Group Associations
    ALB -.-> ALBSG
    Container1 -.-> ECSSG
    Container2 -.-> ECSSG
    
    %% IAM Associations
    Container1 -.-> IAM
    Container2 -.-> IAM
    
    %% Styling
    classDef aws fill:#FF9900,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef vpc fill:#4B9CD3,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef subnet fill:#7AA116,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef container fill:#FF6B35,stroke:#232F3E,stroke-width:2px,color:#fff
    classDef security fill:#D13212,stroke:#232F3E,stroke-width:2px,color:#fff
    
    class ECR,DynamoDB,CloudWatch,IAM,Route53 aws
    class VPC vpc
    class PublicSubnet1,PublicSubnet2,PrivateSubnet1,PrivateSubnet2 subnet
    class Container1,Container2 container
    class ALBSG,ECSSG security
```

## Key Components

### 🌐 **Networking Layer**
- **VPC**: `10.0.0.0/16` - Isolated network environment
- **Public Subnets**: `10.0.1.0/24`, `10.0.2.0/24` - For ALB and NAT Gateway
- **Private Subnets**: `10.0.10.0/24`, `10.0.20.0/24` - For ECS tasks
- **Internet Gateway**: Provides internet access to public subnets
- **NAT Gateway**: Single gateway for cost optimization, provides internet access to private subnets

### ⚖️ **Load Balancing & Routing**
- **Application Load Balancer**: Distributes traffic across ECS tasks
- **Route53**: DNS management for `revolut-api.com`
- **Target Group**: Health checks on `/hello/healthcheck`

### 🐳 **Compute Layer**
- **ECS Cluster**: Container orchestration platform
- **Fargate Tasks**: Serverless containers running the Birthday API
- **Auto Scaling**: Automatic scaling based on demand

### 🗄️ **Data Layer**
- **DynamoDB**: NoSQL database storing user birthdays
- **Table**: `users_birthdays` with username as primary key

### 🔐 **Security & Access**
- **IAM Roles**:
  - ECS Execution Role: For container lifecycle management
  - Application Task Role: For DynamoDB and CloudWatch access
- **Security Groups**:
  - ALB SG: Allows HTTP traffic from internet
  - ECS SG: Allows traffic only from ALB

### 📦 **Container Management**
- **ECR Repository**: Private Docker image registry
- **CloudWatch Logs**: Centralized logging for all containers

### 🔄 **CI/CD Pipeline**
- **GitHub Actions**: Automated testing, building, and deployment
- **Workflow**: Test → Build → Push to ECR → Update ECS Service

## Traffic Flow

1. **User Request**: `revolut-api.com/hello/john` → Route53
2. **DNS Resolution**: Route53 → ALB Public IP
3. **Load Balancing**: ALB → ECS Task (Port 8001)
4. **Application Processing**: FastAPI → DynamoDB query
5. **Response**: DynamoDB → FastAPI → ALB → User

## High Availability Features

- ✅ **Multi-AZ Deployment**: Resources spread across 2 availability zones
- ✅ **Auto Scaling**: ECS service automatically scales based on demand
- ✅ **Health Checks**: ALB monitors application health
- ✅ **Rolling Updates**: Zero-downtime deployments via ECS

## Cost Optimization

- 💰 **Single NAT Gateway**: Shared across all private subnets
- 💰 **Fargate**: Pay only for running containers
- 💰 **DynamoDB On-Demand**: Pay per request model
- 💰 **CloudWatch**: Efficient log retention policies

## Security Best Practices

- 🔒 **Private Subnets**: Application containers not directly accessible from internet
- 🔒 **Security Groups**: Least privilege access rules
- 🔒 **IAM Roles**: Fine-grained permissions for AWS services
- 🔒 **VPC Isolation**: Network-level security boundaries
