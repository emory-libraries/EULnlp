import glob, json, sys, textwrap

# This is just a dirty way for me to grab the json full text files we have for some test works and convert them to text files
# for processing with the calais script.

def main():
    # dirty method to write out fulltext of yellowback.json files.
    filenames = glob.glob('*.json')
    for filename in filenames:
        file = open(filename)
        work = json.load(file)
        write_filename = "%s.txt" % filename.split('.')[0]
        write_file = open(write_filename, 'w')
        write_file.write("\n".join(textwrap.wrap(work['fulltext'].encode("utf-8", "ignore"), 80)))
        write_file.close()

if __name__ == "__main__":
    main()