import sys

# Docs:
# Payment information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0602_generel_EN.pdf
# Agreement information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0603_generel_EN.pdf



from records import Record

for file in sys.argv[1:]:
    print file
    for line in open(file, "r"):
        rec = Record(line)
        #if not rec.isImplemented:
        print rec

