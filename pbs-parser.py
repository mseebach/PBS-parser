import sys

# Docs:
# Payment information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0602_generel_EN.pdf
# Agreement information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0603_generel_EN.pdf



from records import Record, PBSParseException

deliveries = []

for file in sys.argv[1:]:

    delivery = None
    section = None

    for line in open(file, "r"):
        rec = Record(line)

        if rec.is_type(Record.NOT_IMPLEMENTED):
            raise PBSParseException("Unimplemented record: "+line)

        if rec.is_type(Record.DELIVERY_START):
            delivery = rec
            continue

        if (rec.is_type(Record.DELIVERY_END)):
            delivery.end(rec)
            deliveries.append(delivery)
            delivery == None
            continue

        if delivery is None:
            raise PBSParseException("File contains content outside of delivery start/end")

        if (rec.is_type(Record.SECTION_START)):
            section = rec
            continue

        if (rec.is_type(Record.SECTION_END)):
            section.end(rec)
            delivery.append(section)
            section = None
            continue

        if section is None:
            raise PBSParseException("File contains content outside of section start/end")

        if (rec.is_type(Record.PAYLOAD)):
            section.append(rec)
            continue
            
        raise PBSParseException("File contains unrecognized content")

for delivery in sorted(deliveries, key=lambda d:d.createdDate.date):
    print delivery
    for section in delivery.sections:
        print "  ", section
