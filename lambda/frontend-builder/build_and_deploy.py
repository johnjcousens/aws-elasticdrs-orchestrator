"""
Frontend Builder Custom Resource
Builds React application and deploys to S3
"""

import boto3
import json
import os
import shutil
from crhelper import CfnResource

s3 = boto3.client('s3')
cloudfront = boto3.client('cloudfront')
helper = CfnResource()


@helper.create
@helper.update
def create_or_update(event, context):
    """Build and deploy frontend"""
    properties = event['ResourceProperties']
    bucket_name = properties['BucketName']
    distribution_id = properties['DistributionId']
    api_endpoint = properties.get('ApiEndpoint', '')
    user_pool_id = properties.get('UserPoolId', '')
    user_pool_client_id = properties.get('UserPoolClientId', '')
    identity_pool_id = properties.get('IdentityPoolId', '')
    region = properties.get('Region', os.environ.get('AWS_REGION', 'us-west-2'))
    
    print(f"Frontend Builder: Building and deploying to bucket: {bucket_name}")
    print(f"API Endpoint: {api_endpoint}")
    print(f"Region: {region}")
    
    try:
        # Create temporary build directory
        build_dir = '/tmp/frontend-build'
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
        os.makedirs(build_dir)
        
        # Create basic index.html with AWS configuration
        # In production, this would clone the repo and run npm build
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS DRS Orchestration</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f2f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #232f3e;
            border-bottom: 3px solid #ff9900;
            padding-bottom: 10px;
        }}
        .status {{
            background: #e7f6ec;
            border-left: 4px solid #1d8102;
            padding: 15px;
            margin: 20px 0;
        }}
        .config {{
            background: #f7f7f7;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .config h2 {{
            margin-top: 0;
            color: #555;
        }}
        .config-item {{
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }}
        .label {{
            font-weight: bold;
            color: #232f3e;
        }}
        .value {{
            color: #ff9900;
        }}
        .next-steps {{
            background: #fff8e1;
            border-left: 4px solid #ff9900;
            padding: 15px;
            margin: 20px 0;
        }}
        .next-steps ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>AWS DRS Orchestration Platform</h1>
        
        <div class="status">
            <strong>✓ Frontend Deployment Successful</strong>
            <p>The React application placeholder has been deployed. This page will be replaced with the full React SPA in Phase 8-11 of implementation.</p>
        </div>

        <div class="config">
            <h2>AWS Configuration</h2>
            <div class="config-item">
                <span class="label">API Endpoint:</span> 
                <span class="value">{api_endpoint or 'Not configured'}</span>
            </div>
            <div class="config-item">
                <span class="label">Region:</span> 
                <span class="value">{region}</span>
            </div>
            <div class="config-item">
                <span class="label">User Pool ID:</span> 
                <span class="value">{user_pool_id or 'Not configured'}</span>
            </div>
            <div class="config-item">
                <span class="label">User Pool Client ID:</span> 
                <span class="value">{user_pool_client_id or 'Not configured'}</span>
            </div>
            <div class="config-item">
                <span class="label">Identity Pool ID:</span> 
                <span class="value">{identity_pool_id or 'Not configured'}</span>
            </div>
        </div>

        <div class="next-steps">
            <h2>Next Steps for Full Frontend Implementation</h2>
            <ul>
                <li>Implement React 18.3+ application with Material-UI</li>
                <li>Create Cognito authentication components</li>
                <li>Build Protection Groups management interface</li>
                <li>Build Recovery Plans management interface</li>
                <li>Build Execution monitoring dashboard</li>
                <li>Add real-time status updates</li>
                <li>Implement responsive design</li>
            </ul>
        </div>

        <div id="root"></div>
    </div>
    
    <script>
        // AWS Configuration available to JavaScript
        window.AWS_CONFIG = {{
            apiEndpoint: '{api_endpoint}',
            userPoolId: '{user_pool_id}',
            userPoolClientId: '{user_pool_client_id}',
            identityPoolId: '{identity_pool_id}',
            region: '{region}'
        }};
        
        console.log('AWS DRS Orchestration - Frontend Placeholder');
        console.log('AWS Configuration:', window.AWS_CONFIG);
        console.log('Ready for React application deployment');
    </script>
</body>
</html>"""
        
        # Write index.html
        with open(f'{build_dir}/index.html', 'w') as f:
            f.write(index_html)
        
        print(f"Created index.html ({len(index_html)} bytes)")
        
        # Create a simple error page
        error_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS DRS Orchestration - Error</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f2f5;
        }
        .error-container {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        h1 { color: #d13212; }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>404 - Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Return to Home</a>
    </div>
</body>
</html>"""
        
        with open(f'{build_dir}/error.html', 'w') as f:
            f.write(error_html)
        
        print("Created error.html")
        
        # Upload to S3
        print("Uploading files to S3...")
        uploaded_files = []
        
        for root, dirs, files in os.walk(build_dir):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, build_dir)
                s3_key = relative_path.replace('\\', '/')
                
                # Determine content type
                content_type = 'text/html'
                if file.endswith('.js'):
                    content_type = 'application/javascript'
                elif file.endswith('.css'):
                    content_type = 'text/css'
                elif file.endswith('.json'):
                    content_type = 'application/json'
                elif file.endswith('.png'):
                    content_type = 'image/png'
                elif file.endswith('.jpg') or file.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                elif file.endswith('.svg'):
                    content_type = 'image/svg+xml'
                
                # Set cache control based on file type
                cache_control = 'no-cache' if file == 'index.html' else 'max-age=31536000'
                
                s3.upload_file(
                    local_path,
                    bucket_name,
                    s3_key,
                    ExtraArgs={
                        'ContentType': content_type,
                        'CacheControl': cache_control
                    }
                )
                
                uploaded_files.append(s3_key)
                print(f"Uploaded: {s3_key} ({content_type})")
        
        print(f"Upload complete. Total files: {len(uploaded_files)}")
        
        # Invalidate CloudFront cache
        print("Creating CloudFront invalidation...")
        invalidation_response = cloudfront.create_invalidation(
            DistributionId=distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': ['/*']
                },
                'CallerReference': str(context.request_id)
            }
        )
        
        invalidation_id = invalidation_response['Invalidation']['Id']
        print(f"CloudFront invalidation created: {invalidation_id}")
        
        print("Frontend deployment complete!")
        
        return {
            'BucketName': bucket_name,
            'FilesDeployed': len(uploaded_files),
            'InvalidationId': invalidation_id
        }
        
    except Exception as e:
        error_msg = f"Error deploying frontend: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        raise Exception(error_msg)


@helper.delete
def delete(event, context):
    """No-op for Delete - S3 cleanup handles bucket emptying"""
    print("Frontend Builder: Delete event - S3 cleanup handles bucket emptying")
    return None


def lambda_handler(event, context):
    """Main handler for CloudFormation custom resource"""
    print(f"Frontend Builder: Received event: {json.dumps(event, default=str)}")
    helper(event, context)
