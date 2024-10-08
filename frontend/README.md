# Beacon UI

## Development

Place your configuration file in `webapp/src/environments` and name it as `environment.ts` or `enironment.development.ts` based on your development environment. Use the following format.

```ts
export const environment = {
  // set to true on prduction
  production: false,
  auth: {
    region: 'XXXX',
    identityPoolRegion: 'XXXX',
    userPoolId: 'XXXX_YYYYY',
    userPoolWebClientId: 'XXXX',
    authenticationFlowType: 'XXXX',
  },
  api_endpoint_sbeacon: {
    name: 'XXXX',
    endpoint: 'XXXX',
    region: 'XXXX',
  },
};
```

Change to `webapp/` directory and run the following commands to get started. While `npm` workds, we recommend using `pnpm` for a better experience.

```bash
pnpm install
```

To start the development environment, run.

```bash
pnpm start
```

Default development web view runs on `http://localhost:4200`.

## Contributions

Please follow `prettier` formatting styles. You may run the following command to perform project wide code formatting.

```bash
pnpm run pretty
```

## Deployment

You can use terraform to deploy the webapp to cloudfront. Ensure you have a terraform version `v1.5.6` or newer.

Create a `backend.tf` file if you wish to have shared state for collaborative development. Use the following format.

```hcl
terraform {
  backend "s3" {
    bucket         = "bui-terraform-states"
    key            = "bui"
    region         = "ap-southeast-2"
    dynamodb_table = "bui-state-locks"
  }
}
```

You can create a `tfvars` file named `terraform.tfvars` to provide variables to the development. Use the following format.

```tfvars
region = "us-east-1"
common-tags = {
  Tag1 = "tag-1"
}
```

Be sure to create a `terraform workspace` before deployment. This helps you to have multiple deployments with same backend for testing, staging and production.

View the active workspace
```bash
terraform workspace show
```

List the current set of workspaces
```bash
terraform workspace list
```

Create a workshop and activate it
```bash
terraform workspace new dev
```

Deployment plan can be obtained using following command.
```bash
terraform plan
```

Then deploy using following command.
```bash
terraform apply
```
