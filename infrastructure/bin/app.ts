#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "aws-cdk-lib";
import { ComplianceStack } from "../lib/compliance-stack";

const app = new cdk.App();

new ComplianceStack(app, "ComplianceStack", {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT ?? "996561439262",
    region: process.env.CDK_DEFAULT_REGION ?? "us-east-1",
  },
  description: "Compliance Audit Engine — Lambda + SQS + DynamoDB + S3 + Bedrock",
});
