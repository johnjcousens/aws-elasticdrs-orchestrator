// Copyright Amazon.com and Affiliates. All rights reserved.
// This deliverable is considered Developed Content as defined in the AWS Service Terms.

/**
 * Runtime global augmentation for the AWS config object injected by the
 * CloudFormation deployment Lambda. `aws-config.json` is fetched by
 * index.html before the React bundle runs and attached to window under
 * these two symbols — the main module blocks on `configReady` until the
 * fetch settles.
 *
 * This file only declares types; no runtime code.
 */

export {};

declare global {
  interface Window {
    AWS_CONFIG?: {
      Auth: {
        Cognito: {
          region: string;
          userPoolId: string;
          userPoolClientId: string;
          identityPoolId?: string;
          loginWith: {
            email: boolean;
          };
        };
      };
      API: {
        REST: {
          DRSOrchestration: {
            endpoint: string;
            region: string;
          };
        };
      };
    };
    configReady?: Promise<void>;
  }
}
