#!/usr/bin/env python3
"""
CLI script to build search index for a dataset.
Usage: python build_index.py <dataset_id>
"""

import sys
from app.indexer import build_index_for_dataset


def main():
    if len(sys.argv) < 2:
        print("Usage: python build_index.py <dataset_id>")
        sys.exit(1)

    dataset_id = sys.argv[1]
    print(f"Building index for dataset: {dataset_id}")

    try:
        indexer = build_index_for_dataset(dataset_id)
        print(f"✓ Index built successfully!")
        print(f"  - Index: {indexer.index_path}")
        print(f"  - Metadata: {indexer.metadata_path}")
        print(f"  - Patches: {len(indexer.metadata)}")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

