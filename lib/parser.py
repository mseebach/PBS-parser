from records import Record, PBSParseException
import deliveryrecords
import sectionrecords

# Docs:
# Payment information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0602_generel_EN.pdf
# Agreement information - general: http://www.pbs.dk/da/produkter/betalingsservice/Documents/BS_vejledning_DL_0603_generel_EN.pdf

class PBSParser(object):

    def __init__(self):
        self._deliveries = []
        self.clear_filters()

    def __iter__(self):
        return iter(self.sorted_filtered_deliveries())

    def sorted_filtered_deliveries(self):
        return (rec for rec in self.all_records() if self.apply_filters(rec))

    def sorted_deliveries(self):
        return sorted(self._deliveries, key=lambda d:d.createdDate.date)        

    def apply_filters(self, elem):
        for filter in self._filters:
            res = not filter(elem)
            if res:
                return False
        return True

    def filter(self, lmbda):
        self._filters.append(lmbda)
        return self

    def type_filter(self, type):
        self.filter(lambda x: x.is_type(type))
        return self

    def payload_filter(self):
        self.type_filter(Record.PAYLOAD)
        return self

    def transaction_codes_filter(self, *transactionCodes):
        self.payload_filter()
        self.filter(lambda x: x.transactionCode in transactionCodes)
        return self

    def clear_filters(self):
        self._filters = []        

    def all_registrations_exec(self, lmbda):
        self.clear_filters()
        self.transaction_codes_filter(231)
        self.each(lmbda)

    def all_slip_payments_exec(self, lmbda):
        self.clear_filters()
        self.transaction_codes_filter(297)
        self.each(lmbda)

    def all_cancelations_exec(self, lmbda):
        self.clear_filters()
        self.transaction_codes_filter(232,233,234)
        self.each(lmbda)

    def all_exec(self, lmbda):
        self.clear_filters()
        self.each(lmbda)

    def each(self, lmbda):
        for record in self.__iter__():
            lmbda(record)

    def all_records(self):
        for delivery in self.sorted_deliveries():
            yield delivery
            for section in delivery.sections():
                yield section
                for payload in section.payload():
                    yield payload

    def parse(self,file):
        delivery = None
        section = None
        
        for line in file:
            rec = Record(line)
            
            if rec.is_type(Record.NOT_IMPLEMENTED):
                raise PBSParseException("Unimplemented record: "+line)

            if rec.is_type(Record.DELIVERY_START):
                delivery = rec
                continue

            if (rec.is_type(Record.DELIVERY_END)):
                delivery.end(rec)
                self._deliveries.append(delivery)
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
