from fields import StringField, IntField, DateField, FillerField

class RecordType(object):
    def __init__(self,name):
        self.name = name

    def __str__(self):
        return self.name


class Record(object):
    recordTypeMap = { }

    DELIVERY_START = RecordType("Delivery start")
    DELIVERY_END =   RecordType("Delivery end")
    SECTION_START =  RecordType("Section start")
    SECTION_END =    RecordType("Section end")
    PAYLOAD =        RecordType("Payload")
    NOT_IMPLEMENTED = RecordType("Not implemented")

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
        
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "PBSParseException: "+self.message

class RecordImpl(object):

    def __init__(self,line):
        self.init_fields()
        self.line = line
        self.parse()

    def is_type(self, type):
        return type in self.__class__.recordType

    def update_fields(self, fields):
        self.init_fields()
        self.fields.update(fields)

    def init_fields(self):
        if (not hasattr(self,"fields")):
            self.fields = dict(
                systemId   = StringField("SystemID",  0,2).hide(),
                recordType = IntField   ("RecordType",2,3).hide()
                )

    def parse(self):
        for (key,field) in self.fields.items():
            slice = self.line[field.start:field.start+field.length]
            field.set(slice)
        return self

    def __getattr__(self,field):
        if self.__dict__["fields"].has_key(field):
            return self.fields[field].get()

        if self.__dict__.has_key("end_record") and self.__dict__["end_record"].__dict__["fields"].has_key(field):
            return self.__dict__["end_record"].__dict__["fields"][field].get()

        raise AttributeError("{cls} does not have attribute {atr}".format(cls=self.__class__.__name__, atr=field))
            
    def sorted_fields(self):
        return sorted((field,key) for (key,field) in self.fields.items())

    def get_name(self):
        return self.__class__.__name__

    def __str__(self):
        out = "{0}: ".format(self.get_name())
        for (field,key) in self.sorted_fields():
            out += "{fld}: {val}/".format(fld = field.name, val = getattr(self,key)) if not field.is_hidden() else ""
        return out

    def generate_line(self):
        out = ""
        for (field,key) in self.sorted_fields():
            field.set(self.__dict__[key])
            out += field.format();
        return out

class NotImplementedRecord(RecordImpl):
    recordType = [Record.NOT_IMPLEMENTED]
    pass

class PayloadRecordImpl(RecordImpl):
    recordType = [Record.PAYLOAD]

    def __init__(self,line):
        self.update_fields(dict (
                pbsCreditorNumber = IntField  ("PBS Creditor ID",  5,8),
                transactionCode   = IntField  ("Transaction Code",13,4),
                _recordNumber     = FillerField("0", 17, 3)  ## not used
                ) )

        RecordImpl.__init__(self,line)

    def get_amount(self):  # override for payload records that define an amount
        return 0


class NotImplementedPayloadRecord(PayloadRecordImpl):
    recordType = [Record.NOT_IMPLEMENTED, Record.PAYLOAD]
    pass

class DeliveryRecord(RecordImpl):
    Record.registerRecordType(2, lambda line: DeliveryRecord(line))

    recordType = [Record.DELIVERY_START]

    def __init__(self,line):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8).hide(),
                systemCode    = StringField ("System code",  13,3).hide(),
                deliveryType  = IntField    ("Delivery type",16,4),
                deliveryID    = IntField    ("Delivery ID",20,10),
                filler1       = FillerField (" ", 30, 19),
                createdDate   = DateField   ("Creation date", 49),
                filler2       = FillerField (" ", 55, 73)
                ) )

        RecordImpl.__init__(self,line)

        self._sections = []
        self.control_amount = 0
        self.control_payload_record_count = 0

    def sections(self):
        return self._sections

    def append(self, section):
        self._sections.append(section)
        self.control_amount += section.controlAmount
        self.control_payload_record_count += section.payload_count()

    def end(self, end_delivery_record):
        self.end_record = end_delivery_record
        if self.end_record.controlAmount != self.control_amount:
            raise PBSParseException("Control amount does not match, control says to expect {expected}, but I had {actual}"
                                    .format(expected=self.end_record.controlAmount,
                                            actual=self.control_amount))
        if self.end_record.numberOfPayloadRecords != self.control_payload_record_count:
            raise PBSParseException("Control payload record count does not match, control says to expect {expected}, but I counted {actual}"
                                    .format(expected=self.end_record.numberOfPayloadRecords,
                                            actual=self.control_payload_record_count))


class SectionRecord(RecordImpl):
    Record.registerRecordType(12, lambda line: SectionRecord(line))

    recordType = [Record.SECTION_START]

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

        self._payload = []
        self.control_amount = 0

    def payload_count(self):
        return len(self.payload());

    def payload(self):
        return self._payload

    def append(self, payload):
        self._payload.append(payload)
        self.control_amount += payload.get_amount()

    def end(self, end_section_record):
        self.end_record = end_section_record
        if self.end_record.controlAmount != self.control_amount:
            raise PBSParseException("Control amount does not match, control says to expect {expected}, but I had {actual}"
                                    .format(expected=end_record.controlAmount,
                                            actual=self.control_amount))
        if self.end_record.numberOfPayloadRecords != self.payload_count():
            raise PBSParseException("Control payload record count does not match, control says to expect {expected}, but I counted {actual}"
                                    .format(expected=end_record.numberOfPayloadRecords,
                                            actual=self.payload_count()))

class SectionEndRecord(RecordImpl):
    Record.registerRecordType(92, lambda line: SectionEndRecord(line))

    recordType = [Record.SECTION_END]

    def __init__(self,line):
        self.update_fields(dict (
                pbsCreditorNumber = IntField  ("PBS Creditor ID",  5,8),
                sectionType   = IntField    ("Section type",13,4),
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                filler2       = FillerField (" ", 25, 6),
                numberOfPayloadRecords = IntField("Number of Payload records",  31,11),
                controlAmount = IntField    ("Control amount", 42, 15),
                filler4       = FillerField ("0", 57, 11),
                filler5       = FillerField (" ", 68, 15),
                filler6       = FillerField ("0", 83, 11),
                filler7       = FillerField (" ", 94, 34),
                ) )

        RecordImpl.__init__(self,line)

class DeliveryEndRecord(RecordImpl):
    Record.registerRecordType(992, lambda line: DeliveryEndRecord(line))

    recordType = [Record.DELIVERY_END]

    def __init__(self,line):
        self.update_fields(dict (
                dataSupplCVR  = IntField    ("Data Supplier CVR", 5, 8),
                systemCode    = StringField ("System code",  13,3),
                deliveryType  = IntField    ("Delivery type",16,4),
                numberOfSections = IntField ("Number of Sections",20,11),
                numberOfPayloadRecords = IntField("Number of Payload records",  31,11),
                controlAmount = IntField("Payload amount", 42,15),
                filler3       = FillerField ("0", 57, 71)
                ) )

        RecordImpl.__init__(self,line)


class ActivePaymentAgreementRecord(PayloadRecordImpl):
    PayloadRecord.registerRecordType(230, lambda line : ActivePaymentAgreementRecord(line))

    recordType = [Record.PAYLOAD]

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

        PayloadRecordImpl.__init__(self,line)


class PaymentAgreementRegisteredRecord(PayloadRecordImpl):
    PayloadRecord.registerRecordType(231, lambda line : PaymentAgreementRegisteredRecord(line))

    recordType = [Record.PAYLOAD]

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

        PayloadRecordImpl.__init__(self,line)


class PaymentCancelledRecord(PayloadRecordImpl):

    BANK = "bank"
    CREDITOR = "creditor"
    BS = "betalingsservice"
    causes = [BANK,CREDITOR,BS] 

    recordType = [Record.PAYLOAD]

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

        PayloadRecordImpl.__init__(self,line)

    def get_name(self):
        return self.__class__.__name__ + " (cause: "+self.cause+")"


class PaymentByPaymentSlipCompletedRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(297, lambda line : PaymentByPaymentSlipCompletedRecord(line))

    recordType = [Record.PAYLOAD]

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

        PayloadRecordImpl.__init__(self,line)

    def get_amount(self):
        return self.amount
