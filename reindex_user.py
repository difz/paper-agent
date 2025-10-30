#!/usr/bin/env python
"""
Re-index PDFs for a Discord user to fix citation metadata.

Usage:
    python reindex_user.py <discord_user_id>

Example:
    python reindex_user.py 617562932972224547
"""
import sys
from agent.user_store_manager import UserStoreManager
from agent.logging_conf import setup_logging

def main():
    if len(sys.argv) < 2:
        print("Usage: python reindex_user.py <discord_user_id>")
        print("Example: python reindex_user.py 617562932972224547")
        sys.exit(1)

    setup_logging()
    user_id = sys.argv[1]
    manager = UserStoreManager()

    # Check if user has PDFs
    stats = manager.get_user_stats(user_id)
    if stats['pdf_count'] == 0:
        print(f"❌ User {user_id} has no PDFs uploaded.")
        return

    print(f"📚 Found {stats['pdf_count']} PDF(s) for user {user_id}")
    print(f"📄 PDFs: {', '.join(stats['pdf_names'])}")
    print()

    # Ask for confirmation
    response = input(f"Re-index these PDFs? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print("\nRe-indexing PDFs...")
    num_chunks = manager.build_user_index(user_id)

    print(f"\n✅ Successfully indexed {num_chunks} chunks!")

    # Verify
    print("\nVerifying metadata extraction...")
    retriever = manager.get_retriever(user_id)
    if retriever:
        docs = retriever.invoke("test")
        if docs:
            print(f"\n📄 Sample document:")
            print(f"  Title: {docs[0].metadata.get('bib_title')}")
            print(f"  Authors: {docs[0].metadata.get('bib_authors')}")
            print(f"  Year: {docs[0].metadata.get('bib_year')}")
            print(f"\n✨ Citations should now show proper author names!")
        else:
            print("⚠️ No documents found in index.")
    else:
        print("❌ Failed to load index.")

if __name__ == "__main__":
    main()
