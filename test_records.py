import unittest2 as unittest
from records import Record

class TestRecordFactory(unittest.TestCase):

    def test_payload_record_is_created(self):
        line = "BS04202408503023000000001000000000000073856862184011009000000"
        record = Record(line)
        self.assertEquals(record.__class__.__name__, "ActiveAgreementRecord")


if __name__ == '__main__':
    unittest.main()
