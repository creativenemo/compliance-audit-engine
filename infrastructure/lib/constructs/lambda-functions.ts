import * as cdk from "aws-cdk-lib";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as iam from "aws-cdk-lib/aws-iam";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as lambdaEventSources from "aws-cdk-lib/aws-lambda-event-sources";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as sqs from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";

interface Props {
  jobsTable: dynamodb.Table;
  apiKeysTable: dynamodb.Table;
  auditQueue: sqs.Queue;
  indexesBucket: s3.Bucket;
  reportsBucket: s3.Bucket;
  pdfsBucket: s3.Bucket;
  devApiKey: string;
}

export class LambdaFunctionsConstruct extends Construct {
  public readonly apiHandler: lambda.Function;
  public readonly orchestrator: lambda.Function;
  public readonly indexRefresher: lambda.Function;

  constructor(scope: Construct, id: string, props: Props) {
    super(scope, id);

    const commonEnv = {
      JOBS_TABLE_NAME: props.jobsTable.tableName,
      API_KEYS_TABLE_NAME: props.apiKeysTable.tableName,
      AUDIT_QUEUE_URL: props.auditQueue.queueUrl,
      INDEXES_BUCKET: props.indexesBucket.bucketName,
      REPORTS_BUCKET: props.reportsBucket.bucketName,
      PDFS_BUCKET: props.pdfsBucket.bucketName,
      DEV_API_KEY: props.devApiKey,
    };

    // API Handler — FastAPI via Mangum
    this.apiHandler = new lambda.Function(this, "ApiHandler", {
      functionName: "compliance-api-handler",
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset("../backend", {
        exclude: ["tests/", ".venv/", "__pycache__/", "*.pyc"],
      }),
      handler: "app.main.handler",
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      environment: commonEnv,
    });

    // Orchestrator — SQS pipeline runner
    this.orchestrator = new lambda.Function(this, "Orchestrator", {
      functionName: "compliance-orchestrator",
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset("../backend", {
        exclude: ["tests/", ".venv/", "__pycache__/", "*.pyc"],
      }),
      handler: "orchestrator.handler.handler",
      memorySize: 1024,
      timeout: cdk.Duration.minutes(5),
      environment: commonEnv,
    });

    // Wire SQS → orchestrator
    this.orchestrator.addEventSource(
      new lambdaEventSources.SqsEventSource(props.auditQueue, {
        batchSize: 1,
        reportBatchItemFailures: true,
      })
    );

    // Index Refresher — nightly/monthly OFAC+LEIE download
    this.indexRefresher = new lambda.Function(this, "IndexRefresher", {
      functionName: "compliance-index-refresher",
      runtime: lambda.Runtime.PYTHON_3_12,
      code: lambda.Code.fromAsset("../backend", {
        exclude: ["tests/", ".venv/", "__pycache__/", "*.pyc"],
      }),
      handler: "index_refresher.handler.handler",
      memorySize: 512,
      timeout: cdk.Duration.minutes(10),
      environment: commonEnv,
    });

    // Grants — least privilege
    props.jobsTable.grantReadWriteData(this.apiHandler);
    props.apiKeysTable.grantReadData(this.apiHandler);
    props.jobsTable.grantReadWriteData(this.orchestrator);
    props.auditQueue.grantSendMessages(this.apiHandler);
    props.pdfsBucket.grantRead(this.apiHandler);
    props.indexesBucket.grantRead(this.orchestrator);
    props.reportsBucket.grantPut(this.orchestrator);
    props.indexesBucket.grantPut(this.indexRefresher);

    // Bedrock access for orchestrator (Nova calls)
    this.orchestrator.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ["bedrock:InvokeModel"],
        resources: [
          `arn:aws:bedrock:${cdk.Aws.REGION}::foundation-model/amazon.nova-lite-v1:0`,
          `arn:aws:bedrock:${cdk.Aws.REGION}::foundation-model/amazon.nova-pro-v1:0`,
          `arn:aws:bedrock:${cdk.Aws.REGION}::foundation-model/amazon.nova-micro-v1:0`,
        ],
      })
    );
  }
}
