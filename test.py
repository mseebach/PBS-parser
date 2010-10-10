import unittest2 as unittest


if __name__ == '__main__':
    suite = unittest.TestLoader().discover("test")
    unittest.TextTestRunner(verbosity=2).run(suite)
