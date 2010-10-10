import unittest2 as unittest
from lib.records import Record

class TestRecordFactory(unittest.TestCase):

    def test_payload_record_is_created(self):
        line = "BS04202408503023000000001000000000000073856862184011009000000"
        record = Record(line)
        self.assertEquals(record.__class__.__name__, "ActivePaymentAgreementRecord")

    def test_unimplemented_record(self):
        line = "BS01802408503023000000001000000000000073856862184011009000000"
        record = Record(line)
        self.assertTrue(record.is_type(Record.NOT_IMPLEMENTED))

    def test_unimplemented_payload_record(self):
        line = "BS04202408503099900000001000000000000073856862184011009000000"
        record = Record(line)
        self.assertTrue(record.is_type(Record.PAYLOAD))
        self.assertTrue(record.is_type(Record.NOT_IMPLEMENTED))
    
