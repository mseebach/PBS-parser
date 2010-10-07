from fields import StringField, IntField, DateField, FillerField

class Record(object):
    recordTypeMap = { }

    @staticmethod
    def registerRecordType(type,lmbda):
        Record.recordTypeMap[type] = lmbda

    def __new__(klass, line):
        not_found = lambda line: NotImplementedRecord(line)
        return Record.recordTypeMap.get( RecordImpl(line).recordType, not_found )(line)

    def __init__(self, line):
        pass # never reached


class PayloadRecord(object):

    Record.registerRecordType(42, lambda line: PayloadRecord(line))

    transactionCodeMap = { }

    @staticmethod
    def registerRecordType(type,lmbda):
        PayloadRecord.transactionCodeMap[type] = lmbda

    def __new__(klass, line):
        not_found = lambda line: NotImplementedPayloadRecord(line)
        return PayloadRecord.transactionCodeMap.get( PayloadRecordImpl(line).transactionCode, not_found )(line)


class PBSParseException(Exception):
    line = ""
        
    def __init__(self, line):
        self.line = line


class RecordImpl(object):
    isImplemented = True

    def __init__(self,line):
        self.init_fields()
        self.line = line
        self.parse()

    def update_fields(self, fields):
        self.init_fields()
        self.fields.update(fields)

    def init_fields(self):
        if (not hasattr(self,"fields")):
            self.fields = dict(
                systemId   = StringField("SystemID",  0,2),
                recordType = IntField   ("RecordType",2,3)
                )

    def parse(self):
        for (key,field) in self.fields.items():
            slice = self.line[field.start:field.start+field.length]
            field.set(slice)
            self.__dict__[key] = field.get()
        return self

    def sorted_fields(self):
        return sorted((field,key) for (key,field) in self.fields.items())

    def get_name(self):
        return self.__class__.__name__

    def __str__(self):
        out = "{0}: ".format(self.get_name())
        for (field,key) in self.sorted_fields():
            out += "{fld}: {val}/".format(fld = field.name, val = self.__dict__[key]) if not field.filler else ""
        return out

    def generate_line(self):
        out = ""
        for (field,key) in self.sorted_fields():
            field.set(self.__dict__[key])
            out += field.format();
        return out

class NotImplementedRecord(RecordImpl):
    isImplemented = False
    pass

class PayloadRecordImpl(RecordImpl):
    isImplemented = True

    def __init__(self,line):
        self.update_fields(dict (
                pbsCreditorNumber = IntField  ("PBS Creditor ID",  5,8),
                transactionCode   = IntField  ("Transaction Code",13,4),
                _recordNumber     = FillerField("0", 17, 3)  ## not used
                ) )

        RecordImpl.__init__(self,line)

class NotImplementedPayloadRecord(PayloadRecordImpl):
    isImplemented = False
    pass

class DeliveryStartRecord(RecordImpl):
    Record.registerRecordType(2, lambda line: DeliveryStartRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8),
                systemCode    = StringField ("System code",  13,3),
                deliveryType  = IntField    ("Delivery type",16,4),
                deliveryID    = IntField    ("Delivery ID",20,10),
                filler1       = FillerField (" ", 30, 19),
                dateCancelled = DateField   ("Creation date", 49),
                filler2       = FillerField (" ", 55, 73)
                ) )

        RecordImpl.__init__(self,line)

class SectionStartRecord(RecordImpl):
    Record.registerRecordType(12, lambda line: SectionStartRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                pbsCreditorNumber = IntField  ("PBS Creditor ID",  5,8),
                sectionType   = IntField    ("Section type",13,4),
                filler1       = FillerField (" ", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                dataSupplierID= StringField ("User's ID with datasupplier",25,15),
                filler2       = FillerField (" ", 40, 9),
                dateCancelled = DateField   ("Creation date", 49),
                filler3       = FillerField (" ", 55, 73)
                ) )

        RecordImpl.__init__(self,line)

class SectionEndRecord(RecordImpl):
    Record.registerRecordType(92, lambda line: SectionEndRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                pbsCreditorNumber = IntField  ("PBS Creditor ID",  5,8),
                sectionType   = IntField    ("Section type",13,4),
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                filler2       = FillerField (" ", 25, 6),
                numberOfPayloadRecords = IntField("Number of Payload records",  31,11),
                filler3       = FillerField ("0", 42, 15),
                filler4       = FillerField ("0", 57, 11),
                filler5       = FillerField (" ", 68, 15),
                filler6       = FillerField ("0", 83, 11),
                filler7       = FillerField (" ", 94, 34),
                ) )

        RecordImpl.__init__(self,line)

class DeliveryEndRecord(RecordImpl):
    Record.registerRecordType(992, lambda line: DeliveryEndRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8),
                systemCode    = StringField ("System code",  13,3),
                deliveryType  = IntField    ("Delivery type",16,4),
                numberOfSections = IntField ("Number of Sections",20,11),
                numberOfPayloadRecords = IntField("Number of Payload records",  31,11),
                payloadAmount = IntField("Payload amount", 42,15),
                filler3       = FillerField ("0", 57, 71)
                ) )

        RecordImpl.__init__(self,line)


class ActivePaymentAgreementRecord(PayloadRecordImpl):
    PayloadRecord.registerRecordType(230, lambda line : ActivePaymentAgreementRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",    25,15),
                agreementId   = IntField    ("Agreement ID",  40, 9),
                dateInEffect  = DateField   ("In effect", 49),
                dateCancelled = DateField   ("Cancelled on",  55),
                filler2       = FillerField (" ", 61, 67),
               )) 

        RecordImpl.__init__(self,line)


class PaymentAgreementRegisteredRecord(PayloadRecordImpl):
    PayloadRecord.registerRecordType(231, lambda line : PaymentAgreementRegisteredRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",    25,15),
                agreementId   = IntField    ("Agreement ID",  40, 9),
                dateInEffect  = DateField   ("In effect", 49),
                dateCancelled = DateField   ("Cancelled on",  55),
                filler2       = FillerField (" ", 61, 67),
               )) 

        RecordImpl.__init__(self,line)


class PaymentCancelledRecord(PayloadRecordImpl):

    BANK = "bank"
    CREDITOR = "creditor"
    BS = "betalingsservice"
    causes = [BANK,CREDITOR,BS] 

    PayloadRecord.registerRecordType(232, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.BANK))
    PayloadRecord.registerRecordType(233, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.CREDITOR))
    PayloadRecord.registerRecordType(234, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.BS))

    def __init__(self,line, cause):
        self.cause = cause
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",    25,15),
                agreementId   = IntField    ("Agreement ID",  40, 9),
                dateInEffect  = DateField   ("In effect", 49),
                dateCancelled = DateField   ("Cancelled on",  55),
                filler2       = FillerField (" ", 61, 67),
               )) 

        RecordImpl.__init__(self,line)

    def get_name(self):
        return self.__class__.__name__ + " (cause: "+self.cause+")"


class PaymentByPaymentSlipCompletedRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(297, lambda line : PaymentByPaymentSlipCompletedRecord(line))

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                filler2       = FillerField ("0", 25, 4),
                customerId    = IntField    ("Customer ID",  29,15),
                slipType      = IntField    ("Slip type", 44,2),
                rejectFeeCode = IntField    ("Reject fee code", 46,1),
                rejectFeeAmount= IntField   ("Reject fee amount", 47,5),
                paymentDate   = DateField   ("paymentDate", 52),
                signCode      = IntField    ("Sign code", 58,1),
                amount        = IntField    ("Amount", 59,13),
                creditorRef   = StringField ("Creditor Reference", 72,9),
                archiveRef    = StringField ("Archive Reference", 81,22),
                actualPaymentDate = DateField("Actual payment date", 103),
                bookPaymentDate = DateField ("Bookkeeping entry date", 109),
                actualAmount  = IntField    ("Actual amount", 115,13)

               )) 

        RecordImpl.__init__(self,line)
