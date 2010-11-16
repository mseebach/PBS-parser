from fields import StringField, IntField, DateField, LongDateField, FillerField

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
    Record.registerRecordType(52, lambda line: PayloadRecord(line))

    transactionCodeMap = { }

    @staticmethod
    def registerRecordType(type,transactionCode,lmbda):
        if not PayloadRecord.transactionCodeMap.has_key(type):
            PayloadRecord.transactionCodeMap[type] = {}
        PayloadRecord.transactionCodeMap[type][transactionCode] = lmbda

    def __new__(klass, line):
        not_found = lambda line: NotImplementedPayloadRecord(line)
        return PayloadRecord.transactionCodeMap.get( 
            PayloadRecordImpl(line).recordType, not_found 
            ).get( 
            PayloadRecordImpl(line).transactionCode, not_found )(line)


class PBSParseException(Exception):
        
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "PBSParseException: "+self.message

class RecordImpl(object):

    def __init__(self,line):
        self.init_fields()
        self.line = line
        if self.line is not "":
            self.parse()


    def is_type(self, type):
        return type in self.__class__._recordType

    def update_fields(self, fields):
        self.init_fields()
        self.systemId = "BS"
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
            field.parse(slice)
        return self

    def __getattr__(self,field):
        if self.__dict__["fields"].has_key(field):
            return self.fields[field].get()

        if self.__dict__.has_key("end_record") and self.__dict__["end_record"].__dict__["fields"].has_key(field):
            return self.__dict__["end_record"].__dict__["fields"][field].get()

        raise AttributeError("{cls} does not have attribute {atr}".format(cls=self.__class__.__name__, atr=field))

    def __setattr__(self,field,value):
        if field == "fields":
            self.__dict__["fields"] = value
            return 

        if self.__dict__["fields"].has_key(field):
            self.fields[field].set(value)
        else:
            self.__dict__[field] = value
    
            
    def sorted_fields(self):
        return sorted((field,key) for (key,field) in self.fields.items())

    def get_name(self):
        return self.__class__.__name__

    def __str__(self):
        out = "{0}: ".format(self.get_name())
        for (field,key) in self.sorted_fields():
            out += "{fld}: {val}/".format(fld = field.name, val = field.pretty()) if not field.is_hidden() else ""
        return out

    def generate_line(self):
        out = ""
        for (field,key) in self.sorted_fields():
            out += field.format();
        return out

class NotImplementedRecord(RecordImpl):
    _recordType = [Record.NOT_IMPLEMENTED]
    pass

class PayloadRecordImpl(RecordImpl):
    _recordType = [Record.PAYLOAD]

    def __init__(self,line):
        self.update_fields(dict (
                creditorPbsNumber = IntField  ("PBS Creditor ID",  5,8),
                transactionCode   = IntField  ("Transaction Code",13,4),
                ) )

        RecordImpl.__init__(self,line)

    def get_amount(self):  # override for payload records that define an amount
        return 0


class NotImplementedPayloadRecord(PayloadRecordImpl):
    _recordType = [Record.NOT_IMPLEMENTED, Record.PAYLOAD]
    pass



class ActivePaymentAgreementRecord(PayloadRecordImpl):
    PayloadRecord.registerRecordType(42, 230, lambda line : ActivePaymentAgreementRecord(line))

    _recordType = [Record.PAYLOAD]

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
    PayloadRecord.registerRecordType(42, 231, lambda line : PaymentAgreementRegisteredRecord(line))

    _recordType = [Record.PAYLOAD]

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

    _recordType = [Record.PAYLOAD]

    PayloadRecord.registerRecordType(42, 232, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.BANK))
    PayloadRecord.registerRecordType(42, 233, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.CREDITOR))
    PayloadRecord.registerRecordType(42, 234, lambda line : PaymentCancelledRecord(line, PaymentCancelledRecord.BS))

    def __init__(self,line, cause):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",    25,15),
                agreementId   = IntField    ("Agreement ID",  40, 9),
                dateInEffect  = DateField   ("In effect", 49),
                dateCancelled = DateField   ("Cancelled on",  55),
                filler2       = FillerField (" ", 61, 67),
               )) 

        self.cause = cause

        PayloadRecordImpl.__init__(self,line)

    def get_name(self):
        return self.__class__.__name__ + " (cause: "+self.cause+")"


class AutomaticPaymentCompletedRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(42, 236, lambda line : AutomaticPaymentCompletedRecord(line))

    _recordType = [Record.PAYLOAD]

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",  25,15),
                agreementId   = IntField    ("Agreement ID", 40,9),
                transactionDate= DateField  ("transaction date", 49),
                signCode      = IntField    ("Sign code", 55,1),
                amount        = IntField    ("Amount", 56,13),
                creditorRef   = StringField ("Creditor Reference", 69,30),
                filler2       = FillerField (" ", 99, 4),
                actualPaymentDate = DateField("Actual payment date", 103),
                bookPaymentDate = DateField ("Bookkeeping entry date", 109),
                actualAmount  = IntField    ("Actual amount", 115,13)
               )) 

        PayloadRecordImpl.__init__(self,line)

    def get_amount(self):
        return self.amount

class AutomaticPaymentRejectedRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(42, 237, lambda line : AutomaticPaymentRejectedRecord(line))

    _recordType = [Record.PAYLOAD]

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",  25,15),
                agreementId   = IntField    ("Agreement ID", 40,9),
                transactionDate= DateField  ("transaction date", 49),
                signCode      = IntField    ("Sign code", 55,1),
                amount        = IntField    ("Amount", 56,13),
                creditorRef   = StringField ("Creditor Reference", 69,30),
                filler2       = FillerField (" ", 99, 4),
                actualPaymentDate = DateField("Actual payment date", 103),
                bookPaymentDate = DateField ("Bookkeeping entry date", 109),
                actualAmount  = IntField    ("Actual amount", 115,13)
               )) 

        PayloadRecordImpl.__init__(self,line)

    def get_amount(self):
        return self.actualAmount


class AutomaticPaymentCancelledRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(42, 238, lambda line : AutomaticPaymentCancelledRecord(line))

    _recordType = [Record.PAYLOAD]

    def __init__(self,line):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 3),
                debtorGroup   = IntField    ("Debtor Group",  20, 5),
                customerId    = IntField    ("Customer ID",  25,15),
                agreementId   = IntField    ("Agreement ID", 40,9),
                transactionDate= DateField  ("transaction date", 49),
                signCode      = IntField    ("Sign code", 55,1),
                amount        = IntField    ("Amount", 56,13),
                creditorRef   = StringField ("Creditor Reference", 69,30),
                filler2       = FillerField (" ", 99, 4),
                actualPaymentDate = DateField("Actual payment date", 103),
                bookPaymentDate = DateField ("Bookkeeping entry date", 109),
                actualAmount  = IntField    ("Actual amount", 115,13)
               )) 

        PayloadRecordImpl.__init__(self,line)

    def get_amount(self):
        return self.actualAmount


class PaymentByPaymentSlipCompletedRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(42, 297, lambda line : PaymentByPaymentSlipCompletedRecord(line))

    _recordType = [Record.PAYLOAD]

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

class DuePaymentRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(42, 280, lambda line : DuePaymentRecord(line))

    _recordType = [Record.PAYLOAD]

    def __init__(self,line=""):
        self.update_fields(dict (
                filler1       = FillerField ("0", 17, 5),
                debtorGroup   = IntField    ("Debtor Group",  22, 5),
                customerId    = IntField    ("Customer ID",  27,15),
                agreementId   = IntField    ("Agreement ID",  42,9),
                dueDate       = LongDateField("Due date", 51),
                signCode      = IntField    ("Sign code", 59,1),
                amount        = IntField    ("Amount", 60,13),
                creditorRef   = StringField ("Creditor Reference", 73,30),
                filler2       = FillerField ("0", 103, 2),
                filler3       = FillerField (" ", 105, 23)
               )) 

        PayloadRecordImpl.__init__(self,line)

        self.recordType = 42
        self.transactionCode = 280


    def get_amount(self):
        return self.amount

class PaymentTextRecord(PayloadRecordImpl):

    PayloadRecord.registerRecordType(52, 241, lambda line : PaymentTextRecord(line))

    _recordType = [Record.PAYLOAD]

    def __init__(self,line=""):
        self.update_fields(dict (
                recordNumber  = IntField ("Record number", 17, 5),
                debtorGroup   = IntField    ("Debtor Group",  22, 5),
                customerId    = IntField    ("Customer ID",  27,15),
                agreementId   = IntField    ("Agreement ID",  42,9),
                filler1       = FillerField ("1", 52, 1),
                text          = StringField ("Text", 52,60),
                filler2       = FillerField (" ", 112, 16)
               )) 

        PayloadRecordImpl.__init__(self,line)

        self.amount = 0
        self.recordType = 52
        self.transactionCode = 241

    def get_amount(self):
        return self.amount
