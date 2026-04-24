import * as cdk from "aws-cdk-lib";
import * as events from "aws-cdk-lib/aws-events";
import * as eventsTargets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import { ApiGatewayConstruct } from "./constructs/api-gateway";
import { LambdaFunctionsConstruct } from "./constructs/lambda-functions";
import { QueuesConstruct } from "./constructs/queues";
import { StorageConstruct } from "./constructs/storage";
import { TablesConstruct } from "./constructs/tables";

export class ComplianceStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const storage = new StorageConstruct(this, "Storage");
    const tables = new TablesConstruct(this, "Tables");
    const queues = new QueuesConstruct(this, "Queues");

    const functions = new LambdaFunctionsConstruct(this, "Functions", {
      jobsTable: tables.jobsTable,
      auditQueue: queues.auditQueue,
      indexesBucket: storage.indexesBucket,
      reportsBucket: storage.reportsBucket,
      pdfsBucket: storage.pdfsBucket,
      devApiKey: process.env.DEV_API_KEY ?? "dev-key-001",
    });

    new ApiGatewayConstruct(this, "ApiGateway", {
      apiHandler: functions.apiHandler,
    });

    // Nightly OFAC refresh (00:00 UTC)
    new events.Rule(this, "OfacNightlyRule", {
      schedule: events.Schedule.cron({ minute: "0", hour: "0" }),
      targets: [new eventsTargets.LambdaFunction(functions.indexRefresher, {
        event: events.RuleTargetInput.fromObject({ source: "scheduled", "detail-type": "ofac-nightly" }),
      })],
    });

    // Monthly LEIE refresh (1st of month, 01:00 UTC)
    new events.Rule(this, "LeieMonthlyRule", {
      schedule: events.Schedule.cron({ minute: "0", hour: "1", day: "1", month: "*" }),
      targets: [new eventsTargets.LambdaFunction(functions.indexRefresher, {
        event: events.RuleTargetInput.fromObject({ source: "scheduled", "detail-type": "leie-monthly" }),
      })],
    });

    // Outputs
    new cdk.CfnOutput(this, "ApiUrl", {
      value: `https://${this.node.tryGetContext("stage") ?? "dev"}.execute-api.${cdk.Aws.REGION}.amazonaws.com`,
      description: "API Gateway URL",
    });

    new cdk.CfnOutput(this, "JobsTableName", {
      value: tables.jobsTable.tableName,
    });

    new cdk.CfnOutput(this, "AuditQueueUrl", {
      value: queues.auditQueue.queueUrl,
    });
  }
}
