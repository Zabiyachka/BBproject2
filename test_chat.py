#!/usr/bin/env python
"""Test script to verify chat functionality"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bb_project.settings')
django.setup()

from core.models import ChatMessage

# Display all messages in database
print("=" * 60)
print("All Chat Messages in Database:")
print("=" * 60)

messages = ChatMessage.objects.all().order_by('created_at')
if messages.exists():
    for msg in messages:
        print(f"[{msg.created_at}] {msg.session_id[:10]}... ({msg.role}): {msg.content[:100]}")
        print()
else:
    print("No messages found in database")

print("=" * 60)
print(f"Total messages: {messages.count()}")
print("=" * 60)

# Test grouping by session
from django.db.models import Count
sessions = ChatMessage.objects.values('session_id').annotate(count=Count('id')).order_by('-count')
print("\nMessages per session:")
for session in sessions:
    print(f"  Session {session['session_id'][:10]}...: {session['count']} messages")
