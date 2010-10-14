import sys

from lib.parser import PBSParser

parser = PBSParser() 

for file in sys.argv[1:]:
     parser.parse( open(file, "r") )


def reg(rec):
    print "Customer",rec.customerId,"registered on",rec.dateInEffect,"agreement",rec.agreementId

def cancel(rec):
    print rec.cause,"cancelled agreement",rec.agreementId,"for customer",rec.customerId,"on",rec.dateCancelled

def print_record(rec):
     print rec

parser.all_registrations_exec(reg)
parser.all_cancelations_exec(cancel)

parser.all_exec(print_record)
