import * as cdk from "aws-cdk-lib";
import * as s3 from "aws-cdk-lib/aws-s3";
import { Construct } from "constructs";

export class StorageConstruct extends Construct {
  public readonly indexesBucket: s3.IBucket;
  public readonly reportsBucket: s3.IBucket;
  public readonly pdfsBucket: s3.IBucket;

  constructor(scope: Construct, id: string) {
    super(scope, id);

    // Import existing buckets (created during initial deploy attempt)
    this.indexesBucket = s3.Bucket.fromBucketName(
      this, "IndexesBucket",
      `compliance-indexes-${cdk.Aws.ACCOUNT_ID}`,
    );

    this.reportsBucket = s3.Bucket.fromBucketName(
      this, "ReportsBucket",
      `compliance-reports-${cdk.Aws.ACCOUNT_ID}`,
    );

    this.pdfsBucket = s3.Bucket.fromBucketName(
      this, "PdfsBucket",
      `compliance-pdfs-${cdk.Aws.ACCOUNT_ID}`,
    );
  }
}
