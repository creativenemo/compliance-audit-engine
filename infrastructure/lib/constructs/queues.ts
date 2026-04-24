import * as cdk from "aws-cdk-lib";
import * as sqs from "aws-cdk-lib/aws-sqs";
import { Construct } from "constructs";

export class QueuesConstruct extends Construct {
  public readonly auditQueue: sqs.Queue;
  public readonly auditDlq: sqs.Queue;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.auditDlq = new sqs.Queue(this, "AuditDlq", {
      queueName: "audit-jobs-dlq.fifo",
      fifo: true,
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      retentionPeriod: cdk.Duration.days(14),
    });

    this.auditQueue = new sqs.Queue(this, "AuditQueue", {
      queueName: "audit-jobs.fifo",
      fifo: true,
      contentBasedDeduplication: false,
      encryption: sqs.QueueEncryption.SQS_MANAGED,
      visibilityTimeout: cdk.Duration.minutes(5),
      retentionPeriod: cdk.Duration.days(1),
      deadLetterQueue: {
        queue: this.auditDlq,
        maxReceiveCount: 3,
      },
    });
  }
}
