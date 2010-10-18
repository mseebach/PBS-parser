from records import Record, RecordImpl, NotImplementedRecord
from fields import StringField, IntField, DateField, LongDateField, FillerField
from utils import assertEquals

class SectionRecord(object):
    Record.registerRecordType(12, lambda line: SectionRecord(line))

    sectionTypeMap = { }

    @staticmethod
    def registerSectionType(type,lmbda):
        SectionRecord.sectionTypeMap[type] = lmbda

    def __new__(klass, line):
        not_found = lambda line: NotImplementedRecord(line)
        return SectionRecord.sectionTypeMap.get(SectionRecordImpl(line).sectionType, not_found )(line)

class SectionRecordImpl(RecordImpl):
    _recordType = [Record.SECTION_START]

    def __init__(self,line):

        self.update_fields(dict (
                creditorPbsNumber = IntField  ("PBS Creditor ID",  5,8),
                sectionType   = IntField    ("Section type",13,4)
                ) )

        RecordImpl.__init__(self,line)

        self.recordType = 12

        self._payload = []
        self._control_amount = 0

    def payload_count(self):
        return len(self.payload());

    def payload_count_type(self, type):
        return len( [rec for rec in self.payload() if rec.recordType == type] );

    def payload(self):
        return self._payload

    def control_amount(self):
        return self._control_amount

    def append(self, payload):
        self._payload.append(payload)
        self._control_amount += payload.get_amount()

    def end(self, end_section_record):
        self.end_record = end_section_record

        assertEquals("Control payment amount does not match",self.end_record.controlAmount, self.control_amount())

        assertEquals("Control number of payment records does not match",
                     self.end_record.numberOfPaymentRecords,
                     self.payload_count_type(42))

        assertEquals("Control number of auxiliary records does not match",
                     self.end_record.numberOfAuxiliaryRecords, 
                     self.payload_count_type(52) + self.payload_count_type(62))

        assertEquals("Control number of debtor info records does not match",
                     self.end_record.numberOfDebtorInfoRecords, 
                     self.payload_count_type(22))


class RegisteredCancelledPaymentSectionRecord(SectionRecordImpl):
    SectionRecord.registerSectionType(212, lambda line: RegisteredCancelledPaymentSectionRecord(line))

    _recordType = [Record.SECTION_START]

    def __init__(self,line=""):
        self.update_fields(dict (
                filler1       = FillerField (" ", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                internalUserID= StringField ("User's ID with datasupplier",25,15),
                filler2       = FillerField (" ", 40, 9),
                dateCreated   = DateField   ("Creation date", 49),
                filler3       = FillerField (" ", 55, 73)
                ) )

        SectionRecordImpl.__init__(self,line)

        self.sectionType = 212

class ReceivedPaymentsSectionRecord(SectionRecordImpl):
    SectionRecord.registerSectionType(215, lambda line: ReceivedPaymentsSectionRecord(line))

    _recordType = [Record.SECTION_START]

    def __init__(self,line=""):
        self.update_fields(dict (
                filler1       = FillerField (" ", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                internalUserID= StringField ("User's ID with datasupplier",25,15),
                filler2       = FillerField (" ", 40, 9),
                dateCreated   = DateField   ("Creation date", 49),
                filler3       = FillerField (" ", 55, 73)
                ) )

        SectionRecordImpl.__init__(self,line)

        self.sectionType = 215




class PaymentSectionRecord(SectionRecordImpl):
    SectionRecord.registerSectionType(112, lambda line: PaymentSectionRecord(line))

    _recordType = [Record.SECTION_START]

    def __init__(self,line=""):
        self.update_fields(dict (
                filler1       = FillerField (" ", 17, 5),
                debtorGroup   = IntField    ("Debtor Group",  22, 5),
                internalUserID= StringField ("User's ID with datasupplier",27,15),
                filler2       = FillerField (" ", 42, 4),
                dateCreated   = LongDateField("Creation date", 46),
                creditorBankReg = IntField  ("Creditor bank registration",  54, 4),
                creditorBankAcct = IntField ("Creditor bank account",  58, 10),
                mainTextLine  = StringField ("Main text line",68,60),
                ) )

        SectionRecordImpl.__init__(self,line)

        self.sectionType = 112


class SectionEndRecord(RecordImpl):
    Record.registerRecordType(92, lambda line: SectionEndRecord(line))

    _recordType = [Record.SECTION_END]

    def __init__(self,line=""):
        self.update_fields(dict (
                creditorPbsNumber = IntField  ("Creditor PBS ID",  5,8),
                sectionType   = IntField    ("Section type",13,4),
                filler1       = FillerField ("0", 17, 5),
                debtorGroup   = IntField    ("Debtor Group",  22, 5),
                filler2       = FillerField (" ", 27, 4),
                numberOfPaymentRecords = IntField("Number of payment records",  31,11),
                controlAmount = IntField    ("Control amount", 42, 15),
                numberOfAuxiliaryRecords = IntField("Number of aux. records",  57,11),
                filler3       = FillerField (" ", 68, 15),
                numberOfDebtorInfoRecords = IntField("Number of Payload records",  83,11),
                filler4       = FillerField (" ", 94, 34)
                ) )


        self.recordType = 92

        RecordImpl.__init__(self,line)

