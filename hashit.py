# path to python is:  C:\Users\david\miniconda\python.exe
#!C:\users\david\miniconda\python.exe

import hashlib
import os
import sqlite3
import argparse

options = {
    "rename" : False,
    "diff" : False,
    "unrename" : False,
    "flush" : False,
    "recursive" : False
}

numberErrors = 0

def main():

    parser = argparse.ArgumentParser(description="Check for duplicate files in a directory.")
    parser.add_argument("action", choices=["store","check","list", "flush"], help="The action to perform. Options: 'store', 'check', 'list', 'flush'.", default="store")
    parser.add_argument("collection", help="The collection to store the hashes in.", default="hashes")
    parser.add_argument("--recursive", help="Recursively check for duplicates in the child directories as well as this one.", default = False, action="store_true")
    parser.add_argument("--directory", help="The directory to check for duplicates in.", default=os.getcwd(), type=str)
    parser.add_argument("--rename", help="Rename the file if a duplicate is found.", default = False, action="store_true")
    parser.add_argument("--diff", help="Only return files not in the collection", default = False, action="store_true")
    parser.add_argument("--unrename", help="Add this to fix all filenames if renamed by accident.", default = False, action="store_true")
    parser.add_argument("--flush", help="Delete the collection", default = False, action="store_true")
    parser.add_argument("--listonly", help="Only list the files in the collection", default = False, action="store_true")

    args = parser.parse_args()

    options["recursive"] = args.recursive
    options["rename"] = args.rename
    options["diff"] = args.diff
    options["unrename"] = args.unrename
    options["flush"] = args.flush
    options["listonly"] = args.listonly


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

    print(f"Storing hash for file: {filename}...", end="")

    conn = get_connection(collection)
    c = conn.cursor()

    # if the filename already exists in the database, skip it
    c.execute('''SELECT filename FROM file_hashes WHERE filename = ?''', (filename,))
    if c.fetchone():
        print(" (Already exists in collection)")
        return False
    
    # Generate the hash for the file
    hash = sha1(filename)

    if not hash:
        print("❌ getting hash failed!")
        return False

    # Insert or update the hash in the database
    c.execute('''INSERT OR REPLACE INTO file_hashes (filename, hash)
                 VALUES (?, ?)''', (filename, hash))
    
    if c.rowcount == 1:
        print("✅")
    else:
        print("❌ storing hash failed!")


    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    return True


def store_hashes(directory, collection):
    print(f"Storing hashes for files in directory: {directory} into collection {collection}...")
    conn = get_connection(collection)
    c = conn.cursor()


    # Create table for storing hashes if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS file_hashes
                 (filename TEXT, hash TEXT, PRIMARY KEY (filename))''')

    # Generate and store hashes

    global options

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


    print("End of list.")

def check_hashes(collection,args):
    conn = get_connection(collection)
    c = conn.cursor()

    global options

    # get all files in the directory
    for dirpath, dirnames, filenames in os.walk(args.directory):
        for filename in filenames:
            if not os.path.isdir(os.path.join(dirpath, filename)):

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, args.directory)

                if not options["diff"]:
                    if options["recursive"]:
                        print(f"Checking {rel_path} ...", end="")
                    else:
                        print(f"Checking {filename} ...", end="")


                if passed_file_hash_exists(full_path, collection):
                    if options["diff"]:
                        continue

                    if not options["diff"]:
                        print("✅ (Found in collection) ", end="")

                    if args.rename and not args.rename == "False":

                        # if the filename already starts with "duplicate__", skip it
                        if filename.startswith("duplicate__"):
                            print(" (Already renamed)")
                            continue

                        print("Renaming file...")
                        # rename the file
                        new_filename = "duplicate__" + filename 
                        os.rename(filename, new_filename)
                        print(f"File renamed to {new_filename}", end="")
                else:
                    if args.diff:
                        print(f"{rel_path} ", end="")

                    if not options["listonly"]:
                        print("❌ (No duplicate found in collection)", end="")

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
        print(" (😉 - Same file as hashed) ")
        print(hash[0])
        return None
    
    if hash:
        # return the just the filename is if the hash is not None
        return hash[0]


if __name__ == "__main__":
    main()


