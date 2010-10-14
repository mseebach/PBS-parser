from records import Record, RecordImpl, PBSParseException
from fields import StringField, IntField, DateField, LongDateField, FillerField
from utils import assertEquals

class DeliveryRecord(RecordImpl):
    Record.registerRecordType(2, lambda line: DeliveryRecord(line))

    _recordType = [Record.DELIVERY_START]

    def __init__(self,line=""):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8).hide(),
                systemCode    = StringField ("System code",  13,3).hide(),
                deliveryType  = IntField    ("Delivery type",16,4),
                deliveryId    = IntField    ("Delivery ID",20,10),
                filler1       = FillerField (" ", 30, 19),
                createdDate   = DateField   ("Creation date", 49),
                filler2       = FillerField (" ", 55, 73)
                ) )

        self.recordType = 2
        self.systemCode = "BS1"

        RecordImpl.__init__(self,line)

        self._sections = []
        self.control_amount = 0
        self.control_payload_record_count = 0

    def sections(self):
        return self._sections

    def sections_payload_count_type(self, type):
        return sum( [ sec.payload_count_type(type) for sec in self._sections ] )

    def section_count(self):
        return len(self._sections)

    def append(self, section):
        self._sections.append(section)
        self.control_amount += section.controlAmount
        self.control_payload_record_count += section.payload_count()

    def end(self, end_delivery_record):
        self.end_record = end_delivery_record

        assertEquals("Control payment amount does not match",self.end_record.controlAmount, self.control_amount)

        assertEquals("Control section count does not match",self.end_record.numberOfSections, self.section_count())

        assertEquals("Control number of payment records does not match",
                     self.end_record.numberOfPaymentRecords,
                     self.sections_payload_count_type(42))

        assertEquals("Control number of auxiliary records does not match",
                     self.end_record.numberOfAuxiliaryRecords, 
                     self.sections_payload_count_type(52) + self.sections_payload_count_type(62))

        assertEquals("Control number of debtor info records does not match",
                     self.end_record.numberOfDebtorInfoRecords, 
                     self.sections_payload_count_type(22))


class DeliveryEndRecord(RecordImpl):
    Record.registerRecordType(992, lambda line: DeliveryEndRecord(line))

    _recordType = [Record.DELIVERY_END]

    def __init__(self,line=""):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8),
                systemCode    = StringField ("System code",  13,3),
                deliveryType  = IntField    ("Delivery type",16,4),
                numberOfSections = IntField ("Number of Sections",20,11),
                numberOfPaymentRecords = IntField("Number of payment records",  31,11),
                controlAmount = IntField("Payload amount", 42,15), 
                numberOfAuxiliaryRecords = IntField("Number of aux. records",  57,11),
                filler3       = FillerField ("0", 68, 15),
                numberOfDebtorInfoRecords = IntField("Number of Payload records",  83,11),
                filler4       = FillerField ("0", 95, 34)
                ) )

        self.recordType = 992
        self.systemCode = "BS1"

        RecordImpl.__init__(self,line)

