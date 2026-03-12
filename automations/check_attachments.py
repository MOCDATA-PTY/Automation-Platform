#!/usr/bin/env python3
"""
Check attachment sizes in touchpoint templates
"""
import os
import sys
import django

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
django.setup()

from dashboard.models import TouchpointTemplate

def check_attachment_sizes():
    print("📎 Checking touchpoint template attachment sizes...")
    
    templates = TouchpointTemplate.objects.all().order_by('touchpoint_number')
    
    for template in templates:
        print(f"\n📄 TP{template.touchpoint_number}: {template.subject}")
        
        if template.attachment:
            try:
                att_path = template.attachment.path
                att_size = os.path.getsize(att_path)
                att_name = os.path.basename(att_path)
                
                # Convert to MB
                size_mb = att_size / (1024 * 1024)
                
                print(f"   📎 Attachment: {att_name}")
                print(f"   📏 Size: {att_size:,} bytes ({size_mb:.2f} MB)")
                
                # Check if size might cause issues
                if size_mb > 25:
                    print("   ⚠️  WARNING: Attachment > 25MB (Graph API limit)")
                elif size_mb > 4:
                    print("   ⚠️  WARNING: Attachment > 4MB (may need upload session)")
                elif size_mb > 3:
                    print("   💡 INFO: Attachment > 3MB (will trigger upload session)")
                else:
                    print("   ✅ Size OK for direct sending")
                    
            except Exception as e:
                print(f"   ❌ Error reading attachment: {e}")
        else:
            print("   📎 No attachment")

if __name__ == "__main__":
    check_attachment_sizes()