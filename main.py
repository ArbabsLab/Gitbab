import sys
import os
import zlib

def main():
    command = sys.argv[1]

    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    elif command == "cat-file" and sys.argv[2] == "-p":
        blob = sys.argv[3]
        with open(f".git/objects/{blob[0:2]}/{blob[2:]}", "rb") as f:
            blob_data = zlib.decompress(f.read()).decode(encoding="utf-8")
        print(blob_data.split("\0")[1])

    else:
        raise RuntimeError(f"Unknown command #{command}")
    

if __name__ == "__main__":
    main()

