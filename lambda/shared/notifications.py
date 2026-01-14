"""
SNS Notification Helper Module

Provides functions to send formatted notifications for DRS orchestration events.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import boto3

# Initialize SNS client
sns = boto3.client('sns')

# Environment variables for SNS topic ARNs
EXECUTION_TOPIC_ARN = os.environ.get('EXECUTION_NOTIFICATIONS_TOPIC_ARN', '')
DRS_ALERTS_TOPIC_ARN = os.environ.get('DRS_ALERTS_TOPIC_ARN', '')


def send_execution_started(execution_id: str, plan_name: str, wave_count: int, 
                          execution_type: str = 'RECOVERY') -> None:
    """Send notification when execution starts"""
    if not EXECUTION_TOPIC_ARN:
        print("No execution notifications topic configured")
        return
    
    try:
        subject = f"🚀 DRS Execution Started - {plan_name}"
        message = f"""
🚀 AWS DRS Orchestration Execution Started

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Type: {execution_type}
• Total Waves: {wave_count}
• Started At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

The disaster recovery execution has been initiated. You will receive updates as each wave progresses.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent execution started notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution started notification: {e}")


def send_execution_completed(execution_id: str, plan_name: str, 
                            waves_completed: int, duration_seconds: int) -> None:
    """Send notification when execution completes successfully"""
    if not EXECUTION_TOPIC_ARN:
        return
    
    try:
        duration_minutes = duration_seconds // 60
        subject = f"✅ DRS Execution Completed - {plan_name}"
        message = f"""
✅ AWS DRS Orchestration Execution Completed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Waves Completed: {waves_completed}
• Duration: {duration_minutes} minutes ({duration_seconds} seconds)
• Completed At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

All recovery waves have been successfully executed. Please verify the recovered infrastructure.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent execution completed notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution completed notification: {e}")


def send_execution_failed(execution_id: str, plan_name: str, 
                         error_message: str, failed_wave: Optional[int] = None) -> None:
    """Send notification when execution fails"""
    if not EXECUTION_TOPIC_ARN:
        return
    
    try:
        subject = f"❌ DRS Execution Failed - {plan_name}"
        wave_info = f"Wave {failed_wave}" if failed_wave is not None else "Unknown wave"
        message = f"""
❌ AWS DRS Orchestration Execution Failed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Failed At: {wave_info}
• Error: {error_message}
• Failed Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please review the execution logs and take appropriate action to resolve the issue.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent execution failed notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution failed notification: {e}")


def send_execution_paused(execution_id: str, plan_name: str, 
                         paused_before_wave: int, wave_name: str) -> None:
    """Send notification when execution is paused"""
    if not EXECUTION_TOPIC_ARN:
        return
    
    try:
        subject = f"⏸️ DRS Execution Paused - {plan_name}"
        message = f"""
⏸️ AWS DRS Orchestration Execution Paused

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Paused Before: Wave {paused_before_wave} ({wave_name})
• Paused At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

The execution is waiting for manual approval to continue. Use the DRS Orchestration console to resume.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent execution paused notification for {execution_id}")
    except Exception as e:
        print(f"Warning: Failed to send execution paused notification: {e}")


def send_wave_completed(execution_id: str, plan_name: str, wave_number: int, 
                       wave_name: str, servers_launched: int) -> None:
    """Send notification when a wave completes"""
    if not EXECUTION_TOPIC_ARN:
        return
    
    try:
        subject = f"✅ Wave {wave_number} Completed - {plan_name}"
        message = f"""
✅ AWS DRS Orchestration Wave Completed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Wave: {wave_number} ({wave_name})
• Servers Launched: {servers_launched}
• Completed At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Wave {wave_number} has completed successfully. All servers are launched.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent wave completed notification for wave {wave_number}")
    except Exception as e:
        print(f"Warning: Failed to send wave completed notification: {e}")


def send_wave_failed(execution_id: str, plan_name: str, wave_number: int, 
                    wave_name: str, failed_servers: int) -> None:
    """Send notification when a wave fails"""
    if not EXECUTION_TOPIC_ARN:
        return
    
    try:
        subject = f"❌ Wave {wave_number} Failed - {plan_name}"
        message = f"""
❌ AWS DRS Orchestration Wave Failed

Execution Details:
• Execution ID: {execution_id}
• Recovery Plan: {plan_name}
• Wave: {wave_number} ({wave_name})
• Failed Servers: {failed_servers}
• Failed At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

Wave {wave_number} has failed. {failed_servers} server(s) failed to launch.
Please review the DRS console for detailed error information.
"""
        
        sns.publish(
            TopicArn=EXECUTION_TOPIC_ARN,
            Subject=subject,
            Message=message
        )
        print(f"✅ Sent wave failed notification for wave {wave_number}")
    except Exception as e:
        print(f"Warning: Failed to send wave failed notification: {e}")
