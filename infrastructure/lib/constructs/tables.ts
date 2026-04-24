import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { Construct } from "constructs";

export class TablesConstruct extends Construct {
  public readonly jobsTable: dynamodb.Table;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.jobsTable = new dynamodb.Table(this, "JobsTable", {
      tableName: "compliance-jobs",
      partitionKey: { name: "job_id", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "sk", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      encryption: dynamodb.TableEncryption.AWS_MANAGED,
      timeToLiveAttribute: "ttl",
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // GSI for querying by status (monitoring, ops)
    this.jobsTable.addGlobalSecondaryIndex({
      indexName: "status-createdAt-index",
      partitionKey: { name: "status", type: dynamodb.AttributeType.STRING },
      sortKey: { name: "created_at", type: dynamodb.AttributeType.STRING },
      projectionType: dynamodb.ProjectionType.INCLUDE,
      nonKeyAttributes: ["job_id", "updated_at", "current_step"],
    });
  }
}
