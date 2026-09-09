# Azure ML Cost Optimization Role

An Ansible role to optimize Azure ML/AI infrastructure costs through automated lifecycle management.

## Features

- Shutdown/startup compute clusters
- Right-size VM instances based on utilization metrics
- Manage Azure OpenAI PTU allocation
- Generate ROI reports
- Comprehensive audit logging

## Usage

Set the `azure_ml_cost_optimization_operation` variable to specify which operation to run:

- `shutdown_compute`: Shut down idle clusters
- `startup_compute`: Start compute clusters
- `analyze_and_rightsize`: Analyze and recommend VM size changes
- `manage_ptu`: Manage Azure OpenAI PTU allocation
- `generate_roi_report`: Generate cost optimization ROI report

## Requirements

- Ansible >= 2.14.0
- azure.azcollection collection
- Valid Azure credentials configured

## Variables

See `defaults/main.yml` for all available variables and their descriptions.
