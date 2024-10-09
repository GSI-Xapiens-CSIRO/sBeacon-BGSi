# sBeacon Infrastructure

<div align="center">
    <img src="./backend/assets/logo-black.png" width="800px">
</div>

## Deployment

Please build the projects first, by following instructions in respective `README` documents.

1. [Backend README](./backend/README.md)
2. [Frontend README](./frontend/README.md)

## Terraform States

Maintaining a `backend.tf` at the top level is essential for conflict free deployments by multiple individuals. Do not create `backend.tf` file in any subfolder.

## Terraform Outputs/Variables

Outputs (resource identifiers, names, arns) will be crucial for the integration of sBeacon with other systems. Please update `outputs.tf` as required.

For eg:
- If you need to output any of the bucket names for some reason, add it to `output.tf` files in either `frontend` or `backend`, then add it to `output.tf` at the top level. This will be available as a module output when you use the entire `sbeacon` infrastructure as a module in a bigger setting.
- If you wanted to move out cognito pool from this project, add those authorizer arns, pool ids, etc as variables. Defined them in `variables.tf` files in `backend` and `frontend`. Add them to `variables.tf` at top level tool. Now this will be a module input when you use `sbeacon` as a module in a bigger setting.
 