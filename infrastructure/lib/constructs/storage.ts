import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export class StorageConstruct extends Construct {
  public readonly indexesBucket: s3.Bucket;
  public readonly reportsBucket: s3.Bucket;
  public readonly pdfsBucket: s3.Bucket;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    this.indexesBucket = new s3.Bucket(this, "IndexesBucket", {
      bucketName: `compliance-indexes-${cdk.Aws.ACCOUNT_ID}`,
      versioned: false,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    this.reportsBucket = new s3.Bucket(this, "ReportsBucket", {
      bucketName: `compliance-reports-${cdk.Aws.ACCOUNT_ID}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(90),
          id: "delete-raw-snapshots-90d",
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    this.pdfsBucket = new s3.Bucket(this, "PdfsBucket", {
      bucketName: `compliance-pdfs-${cdk.Aws.ACCOUNT_ID}`,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [
        {
          expiration: cdk.Duration.days(365),
          id: "delete-pdfs-1yr",
        },
      ],
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });
  }
}
