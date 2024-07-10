import hashlib
import os
import sqlite3
import argparse

python_path = os.environ.get("PYTHON_PATH")
if python_path:
    python_interpreter = os.path.join(python_path, "python.exe")
else:
    python_interpreter = "/usr/bin/python"

#!$python_interpreter$

options = {
    "rename" : False,
    "diff" : False,
    "unrename" : False,
    "flush" : False,
    "recursive" : False,
    "delete" : False,
    "move" : False,
}

numberErrors = 0


def main():

    parser = argparse.ArgumentParser(description="Check for duplicate files in a directory.")
    parser.add_argument("action", choices=["store","check","list","flush", "moveduplicates"], help="The action to perform. Options: 'store', 'check', 'list', 'flush', 'moveduplicates'.  The moveduplicates action does not require or use a collection.", default="store")
    parser.add_argument("collection", help="The collection to store the hashes in.", default="hashes")
    parser.add_argument("--recursive", help="Recursively check for duplicates in the child directories as well as this one.", default = False, action="store_true")
    parser.add_argument("--directory", help="The directory to check for duplicates in.", default=os.getcwd(), type=str)
    parser.add_argument("--rename", help="Rename the file if a duplicate is found.", default = False, action="store_true")
    parser.add_argument("--move", help="Move the file to duplicates subdirectory if found in collection.", default = False, action="store_true")
    parser.add_argument("--diff", help="Only return files not in the collection", default = False, action="store_true")
    parser.add_argument("--unrename", help="Add this to fix all filenames if renamed by accident.", default = False, action="store_true")
    parser.add_argument("--flush", help="Delete the collection", default = False, action="store_true")
    parser.add_argument("--listonly", help="Only list the files in the collection", default = False, action="store_true")
    parser.add_argument("--delete", help="Delete the file if a duplicate is found.", default = False, action="store_true") 
    parser.add_argument("--verbose", help="Print more information.", default = False, action="store_true")
    parser.add_argument("--remove", help="Remove a file's hash from a collection (used with store)", default = False, action="store_true")



    args = parser.parse_args()

    options["recursive"] = args.recursive
    options["rename"] = args.rename
    options["move"] = args.move
    options["diff"] = args.diff
    options["unrename"] = args.unrename
    options["flush"] = args.flush
    options["listonly"] = args.listonly
    options["delete"] = args.delete
    options["verbose"] = args.verbose
    options["remove"] = args.remove

    # moveduplicates action
    if args.action == "moveduplicates":
        # just use a temporary list, not a collection
        dupehashes = []
        duplicate_directory = "duplicates"
        directory = os.getcwd()
        for filename in os.listdir(directory):
            if not os.path.isdir(os.path.join(directory, filename)):
                hash = sha1(filename)
                if hash not in dupehashes:
                    dupehashes.push(hash)
                else:
                    if not os.path.exists(hashes_directory):
                        os.makedirs(hashes_directory)
                        full_path = os.path.join(directory, filename)
                        new_path = os.path.join(directory,duplicate_directory)
                        os.rename(full_path, new_path)
                        print(f" (Moved to {new_path})", end="", flush=True)
        exit(0)

    # speclialized actions 
    if options["unrename"]:
        unrename_files(args.directory)
        print("Done.")
        exit(0)

    if args.action == "flush":
        user_directory = os.path.expanduser("~")
        hashes_directory = os.path.join(user_directory, ".hashes")
        database_path = os.path.join(hashes_directory, args.collection + ".sqlite")
        os.remove(database_path)
        print(f"Collection {args.collection} has been deleted.")
        exit(0)

    # standard actions
    if args.action == "store":
        store_hashes(args.directory, args.collection)
    elif args.action == "check":
        check_hashes(args.collection, args)
    elif args.action == "list":
        list_hashes(args.collection)
    else:
        print(f"Invalid action: {args.action}")

def print_legend():
    print("┌───────────────────────────────────────────┐")
    print("│              Legend:                      │")
    print("│                                           │")
    print("│   ✅ - File found in collection           │")
    print("│   ❌ - File not found in collection       │")
    print("│   🗑️ - File deleted                       │")
    print("│   📂 - File moved to duplicates directory │")
    print("│   😉 - Same path as added to collection   │")
    print("│   🔄 - File already renamed               │")
    print("│   ©️ - File renamed                       │")
    print("│   🚫 - File removed from collection       │")
    print("│                                           │")
    print("└───────────────────────────────────────────┘")
    

def unrename_files(directory):
    for filename in os.listdir(directory):
        if filename.startswith("duplicate__ "):
            new_filename = filename.replace("duplicate__ ", "")
            os.rename(filename, new_filename)
            print(f"File {filename} renamed to {new_filename}")

def collection_exists(collection):
    user_directory = os.path.expanduser("~")
    hashes_directory = os.path.join(user_directory, ".hashes")
    database_path = os.path.join(hashes_directory, collection + ".sqlite")
    return os.path.exists(database_path)

def get_connection(collection):
    # Get the user's home directory
    user_directory = os.path.expanduser("~")
    hashes_directory = os.path.join(user_directory, ".hashes")

    # Create the directory if it doesn't exist
    if not os.path.exists(hashes_directory):
        os.makedirs(hashes_directory)

    database_path = os.path.join(hashes_directory, collection + ".sqlite")

    # Database connection setup
    return sqlite3.connect(database_path)

def store_file_hash(filename, collection):
    global options

    if options["verbose"]:
        print(f"Storing hash for file: {filename}...", end="", flush=True)

    conn = get_connection(collection)
    c = conn.cursor()

    # if the filename already exists in the database, skip it
    c.execute('''SELECT filename FROM file_hashes WHERE filename = ?''', (filename,))
    if c.fetchone():
        if options["verbose"]:
            print(" (Already exists in collection)")
        return False
    
    # Generate the hash for the file
    hash = sha1(filename)

    if not hash:
        print("❌ getting hash failed!")
        return False

    # Insert, update, or delete the hash in the database

    c.execute('''INSERT OR REPLACE INTO file_hashes (filename, hash) VALUES (?, ?)''', (filename, hash))
    
    if c.rowcount == 1:
        print("✅", end="", flush=True)
    else:
        print("❌", end="", flush=True)
        if options["verbose"]: print(" storing hash failed!")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return True

def remove_file_hash(filename, collection):
    global options

    if options["verbose"]:
        print(f"Removing hash for file: {filename}...", end="", flush=True)

    conn = get_connection(collection)
    c = conn.cursor()

    # if the filename doesn't exist in the database, skip it
    c.execute('''SELECT filename FROM file_hashes WHERE filename = ?''', (filename,))
    if not c.fetchone():
        if options["verbose"]:
            print(" (Not found in collection)")
        return False

    # Delete the hash from the database
    c.execute('''DELETE FROM file_hashes WHERE filename = ?''', (filename,))
    
    if c.rowcount == 1:
        print("🚫", end="", flush=True)
    else:
        print("❌", end="", flush=True)
        if options["verbose"]: print(" removing hash failed!")

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return True


def store_hashes(directory, collection):
    global options

    if options["verbose"]:
        print(f"Storing hashes for files in directory: {directory} into collection {collection}...")

    conn = get_connection(collection)
    c = conn.cursor()

    # Create table for storing hashes if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS file_hashes
                 (filename TEXT, hash TEXT, PRIMARY KEY (filename))''')

    # Generate and store hashes
    if options["recursive"]:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                if not os.path.isdir(os.path.join(dirpath, filename)):
                    store_file_hash(os.path.join(dirpath, filename), collection)
    else:
        for filename in os.listdir(directory):
            if not os.path.isdir(os.path.join(directory, filename)):
                store_file_hash(os.path.join(directory, filename), collection)

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print(f"Hashes generated and stored in SQLite database successfully for directory: {directory}")

    if numberErrors > 0:
        print(f"Number of errors: {numberErrors}  (Probably due to permission errors when reading files.)")

def list_hashes(collection):
    
    if not collection_exists(collection):
        print(f"Collection {collection} does not exist.")
        exit(0)

    conn = get_connection(collection)
    c = conn.cursor()

    # if the table doesn't exist, print a message and exit
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='file_hashes';''')
    if not c.fetchone():
        print("Collection is empty.")
        conn.close()
        exit(0)

    # if the collection is empty, print a message and exit
    c.execute('''SELECT COUNT(*) FROM file_hashes''')
    count = c.fetchone()[0]
    if count == 0:
        print("Collection is empty.")
        conn.close()
        exit(0)

    # List the collection of hashes
    c.execute('''SELECT filename,hash FROM file_hashes''')
    hashes = c.fetchall()
    conn.close()

    for filename, hash in hashes:
        print(f"{filename} - {hash}")

    if options["verbose"]:
        print("End of list.")

def check_hashes(collection,args):
    conn = get_connection(collection)
    c = conn.cursor()

    global options

    if not options["verbose"]:
        print_legend()

    # get all files in the directory
    for dirpath, dirnames, filenames in os.walk(args.directory):
        for filename in filenames:
            if not os.path.isdir(os.path.join(dirpath, filename)):

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, args.directory)

                if not options["diff"]:
                    if options["recursive"]:
                        if options["verbose"]: print(f"Checking {rel_path} ...", end="", flush=True)
                    else:
                        if options["verbose"]: print(f"Checking {filename} ...", end="", flush=True)

                pfe = passed_file_hash_exists(full_path, collection)

                if pfe:

                    if pfe == "SAMEFILE":
                        if options["verbose"]:
                            print(" (😉 - Same file as hashed) ")

                        if options["remove"]:
                            remove_file_hash(full_path, collection)

                        continue

                    if options["diff"]:
                        continue

                    if options["verbose"]:
                        print(" (Found in collection) ", end="", flush=True)
                    else:
                        print("✅", end="", flush=True)

                    if options["remove"]:
                        remove_file_hash(full_path, collection)
                        continue

                    if options["delete"]:
                        
                        if options["verbose"]:
                            print(" (Deleting file...)", end="", flush=True)

                        os.remove(full_path)

                        if options["verbose"]:
                            print("✅ (File deleted)", end="", flush=True)
                        else: 
                            print("🗑️", end="", flush=True)

                    if args.rename and not args.rename == "False":

                        # if the filename already starts with "duplicate__", skip it
                        if filename.startswith("duplicate__"):
                            if options["verbose"]:
                                print(" (Already renamed)")
                            else:
                                print("🔄", end="", flush=True)
                            continue

                        print("Renaming file...")
                        # rename the file
                        new_filename = "duplicate__" + filename 
                        os.rename(filename, new_filename)

                        if options["verbose"]:
                            print(f"File renamed to {new_filename}", end="", flush=True)
                        else:
                            print("©️", end="", flush=True)

                    if args.move and not args.move == "False":
                        # create a duplicates directory if it doesn't exist
                        duplicates_dir = os.path.join(args.directory, "duplicates")
                        if not os.path.exists(duplicates_dir):
                            os.makedirs(duplicates_dir)

                        # move the file to the duplicates directory
                        new_path = os.path.join(duplicates_dir, filename)
                        os.rename(full_path, new_path)
                        if options["verbose"]:
                            print(f" (Moved to {new_path})", end="", flush=True)
                        else:
                            print("📂", end="", flush=True)
                else:
                    if args.diff:
                        print(f"{rel_path} ", end="", flush=True)

                    if not options["listonly"]:
                        if options["verbose"]:
                            print("❌ (Not found in collection) ", end="", flush=True)
                        else:
                            print("❌", end="", flush=True)
                        

            if options["verbose"]:
                print("")

        if not options["recursive"]:
            break

    conn.close()


def sha1(fname):
    global numberErrors
    hash_sha1 = hashlib.sha1()
    try:
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha1.update(chunk)
    except PermissionError:
        print(f"Permission denied: {fname}")
        numberErrors += 1
        return None
    except FileNotFoundError:
        print(f"File not found: {fname}")
        numberErrors += 1
        return None

    return hash_sha1.hexdigest()

def passed_file_hash_exists(file_path, collection):
    conn = get_connection(collection)
    c = conn.cursor()

    # generate hash for the file
    hash = sha1(file_path)

    # Find duplicates by sha1 hash
    c.execute('''SELECT filename,hash FROM file_hashes WHERE hash = ?''', (hash,))
    
    hash = c.fetchone()
    conn.close()

    # if the filename is the same as the file_path, then it's the same file
    if hash and hash[0] == file_path:
        if options["verbose"]:
            print(" (😉 - Same file as hashed) ")
        else:
            print("😉", end="", flush=True)

        if options["verbose"]:
            print(hash[0])
        return "SAMEFILE"
    
    if hash:
        # return the just the filename is if the hash is not None
        return hash[0]


if __name__ == "__main__":
    main()


