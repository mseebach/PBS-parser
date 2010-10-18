from records import DuePaymentRecord, PaymentTextRecord
from deliveryrecords import DeliveryRecord, DeliveryEndRecord
from sectionrecords import PaymentSectionRecord, SectionEndRecord

import datetime 
import time

class PBSBuilder(object):
    
    def delivery(self,dataSupplCVR,creditorPbsNumber):
        return DeliveryBuilder(dataSupplCVR,creditorPbsNumber)

class DeliveryBuilder(object):
    
    def __init__(self,dataSupplCVR,creditorPbsNumber):
        self.dataSupplCVR=dataSupplCVR
        self.creditorPbsNumber=creditorPbsNumber
        self.delivery = self.start_record()
        self.section_count = 0
        self.payload_count = 0
        self.control_amount = 0
        self.payment_rec_count = 0
        self.auxiliary_rec_count = 0
        self.debtorinfo_rec_count = 0

    def payment_section(self,internalUserID,creditorBankReg,creditorBankAcct,mainTextLine,debtorGroup=1):
        return SectionBuilder(self,internalUserID,creditorBankReg,creditorBankAcct,mainTextLine,debtorGroup)

    def append(self,section):
        self.delivery.append(section)
        self.section_count += 1
        self.payload_count += section.payload_count()
        self.payment_rec_count +=    section.payload_count_type(42)
        self.auxiliary_rec_count +=  section.payload_count_type(52) + section.payload_count_type(62)
        self.debtorinfo_rec_count += section.payload_count_type(22)
        self.control_amount += section.control_amount()

    def start_record(self):
        start = DeliveryRecord()
        start.dataSupplCVR = self.dataSupplCVR
        start.deliveryType = 601
        start.deliveryId = int(time.time())
        start.createdDate = datetime.datetime.today()
        return start

    def end_record(self):
        end = DeliveryEndRecord()
        end.dataSupplCVR=self.dataSupplCVR
        end.deliveryType = 601
        end.numberOfSections = self.section_count
        end.numberOfPaymentRecords = self.payment_rec_count
        end.numberOfAuxiliaryRecords = self.auxiliary_rec_count
        end.numberOfDebtorInfoRecords = self.debtorinfo_rec_count
        end.controlAmount = self.control_amount
        self.delivery.end(end)

    def build(self):
        self.end_record()
        return self.delivery

    def write_file(self, filename):
        f = open(filename, "w")
        for record in self.all_records():
            f.write(record.generate_line()+"\n")
        
    def all_records(self):
        yield self.delivery
        for section in self.delivery.sections():
            yield section
            for payload in section.payload():
                yield payload  
            yield section.end_record
        yield self.delivery.end_record

class SectionBuilder(object):
    
    def __init__(self,delivery,internalUserID,creditorBankReg,creditorBankAcct,mainTextLine,debtorGroup):
        self.delivery=delivery
        self.debtorGroup=debtorGroup
        self.internalUserID=internalUserID
        self.creditorBankReg=creditorBankReg
        self.creditorBankAcct=creditorBankAcct
        self.mainTextLine=mainTextLine
        self.recordCounter = 1
        self.section = self.start_record()

    def due_automatic_payment(self,customerId,agreementId,dueDate,amount):
        self.customerId = customerId
        self.agreementId = agreementId
        self.recordCounter = 1

        rec = DuePaymentRecord()
        rec.creditorPbsNumber = self.delivery.creditorPbsNumber
        rec.debtorGroup = self.debtorGroup
        rec.customerId=customerId
        rec.agreementId=agreementId
        rec.dueDate=dueDate
        rec.signCode=1
        rec.amount=amount
        self.section.append(rec)

    def text(self,txt):
        rec = PaymentTextRecord()
        rec.creditorPbsNumber = self.delivery.creditorPbsNumber
        rec.recordNumber = self.recordCounter
        rec.debtorGroup = self.debtorGroup
        rec.customerId=self.customerId
        rec.agreementId=self.agreementId
        rec.text = txt
        self.section.append(rec)
        
        self.recordCounter += 1

    def start_record(self):
        rec = PaymentSectionRecord()
        rec.creditorPbsNumber = self.delivery.creditorPbsNumber
        rec.debtorGroup = self.debtorGroup
        rec.internalUserID = self.internalUserID
        rec.dateCreated = datetime.datetime.today()
        rec.creditorBankReg=self.creditorBankReg
        rec.creditorBankAcct=self.creditorBankAcct
        rec.mainTextLine=self.mainTextLine
        return rec 

    def end_record(self):
        rec = SectionEndRecord()
        rec.creditorPbsNumber = self.delivery.creditorPbsNumber
        rec.sectionType = self.section.sectionType
        rec.debtorGroup = self.debtorGroup

        rec.numberOfPaymentRecords = self.section.payload_count_type(42)
        rec.numberOfAuxiliaryRecords = self.section.payload_count_type(52) + self.section.payload_count_type(62)
        rec.numberOfDebtorInfoRecords = self.section.payload_count_type(22)

        rec.controlAmount = self.section.control_amount()
        self.section.end(rec)

    def build(self):
        self.end_record()
        return self.section
