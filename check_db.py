#!/usr/bin/env python
"""Quick database check"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bb_project.settings')
django.setup()

from core.models import ChatMessage

print("\n" + "="*60)
print("CHAT MESSAGES IN DATABASE:")
print("="*60)

messages = ChatMessage.objects.all().order_by('-created_at')[:20]
if messages:
    for msg in messages:
        content = msg.content[:80].replace('\n', ' ')
        print(f"[{msg.created_at}] Session: {msg.session_id[:12]}...")
        print(f"  Role: {msg.role:10} | Content: {content}")
        print()
else:
    print("No messages found")

print("="*60)
print(f"Total messages: {ChatMessage.objects.count()}")
print("="*60 + "\n")
