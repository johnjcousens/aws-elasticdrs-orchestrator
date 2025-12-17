#!/usr/bin/env python3

import requests
import json
import sys

# Test the enhanced tag-based server query
def test_tag_query():
    # API endpoint
    api_url = "https://baju5jevwe.execute-api.us-east-1.amazonaws.com/dev/protection-groups/query-servers-by-tags"
    
    # Test with known tags from us-west-2
    test_payload = {
        "region": "us-west-2",
        "tags": {
            "DR-Application": "HRP"
        }
    }
    
    print("Testing enhanced tag-based server query...")
    print(f"URL: {api_url}")
    print(f"Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(api_url, json=test_payload, timeout=30)
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            servers = data.get('servers', [])
            print(f"Found {len(servers)} servers")
            
            if servers:
                print("\nFirst server details:")
                server = servers[0]
                print(f"  Server ID: {server.get('sourceServerID')}")
                print(f"  Hostname: {server.get('hostname')}")
                print(f"  FQDN: {server.get('fqdn')}")
                print(f"  State: {server.get('state')}")
                print(f"  Source IP: {server.get('sourceIp')}")
                print(f"  Source Region: {server.get('sourceRegion')}")
                
                # Check hardware details
                hardware = server.get('hardware', {})
                if hardware:
                    print(f"\nHardware Details:")
                    print(f"  CPU Cores: {hardware.get('totalCores')}")
                    print(f"  RAM: {hardware.get('ramGiB')} GiB ({hardware.get('ramBytes')} bytes)")
                    print(f"  Total Disk: {hardware.get('totalDiskGiB')} GiB")
                    
                    cpus = hardware.get('cpus', [])
                    if cpus:
                        print(f"  CPU Model: {cpus[0].get('modelName')}")
                    
                    disks = hardware.get('disks', [])
                    if disks:
                        print(f"  Disk Count: {len(disks)}")
                        for i, disk in enumerate(disks[:3]):  # Show first 3 disks
                            print(f"    Disk {i+1}: {disk.get('deviceName')} - {disk.get('sizeGiB')} GiB")
                else:
                    print("  ❌ No hardware details found")
                
                # Check network interfaces
                network_interfaces = server.get('networkInterfaces', [])
                if network_interfaces:
                    print(f"\nNetwork Interfaces: {len(network_interfaces)}")
                    for i, nic in enumerate(network_interfaces[:2]):  # Show first 2 NICs
                        print(f"  NIC {i+1}: {', '.join(nic.get('ips', []))} ({nic.get('macAddress')})")
                
                # Check tags
                tags = server.get('tags', {}) or server.get('drsTags', {})
                if tags:
                    print(f"\nTags: {len(tags)}")
                    for key, value in list(tags.items())[:5]:  # Show first 5 tags
                        print(f"  {key}: {value}")
                
                print(f"\n✅ Enhanced server data structure looks good!")
            else:
                print("No servers found matching the tags")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_tag_query()